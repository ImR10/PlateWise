/**
 * Unit tests for the minimal API client: JSON handling, standard-envelope
 * error parsing, cancellation, and the auth-header seam. All requests go
 * through an injected fetch stub — no network.
 */
import { describe, expect, it, vi } from "vitest";

import { ApiRequestError, createApiClient } from "./client";

const BASE = "http://api.test";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function requestHeaders(fetchImpl: ReturnType<typeof vi.fn>): Headers {
  return new Headers(fetchImpl.mock.calls[0][1].headers);
}

describe("createApiClient", () => {
  it("performs a GET and returns parsed JSON", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse({ status: "ok" }));
    const client = createApiClient({ baseUrl: BASE, fetchImpl });

    const result = await client.get<{ status: string }>("/api/v1/status");

    expect(result).toEqual({ status: "ok" });
    const [url, init] = fetchImpl.mock.calls[0];
    expect(url).toBe(`${BASE}/api/v1/status`);
    expect(init.method).toBe("GET");
    expect(requestHeaders(fetchImpl).get("accept")).toBe("application/json");
    expect(init.body).toBeUndefined();
  });

  it("serializes JSON bodies and sets Content-Type for POST", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse({ id: "1" }, 200));
    const client = createApiClient({ baseUrl: BASE, fetchImpl });

    await client.post("/api/v1/things", { name: "A" });

    const [, init] = fetchImpl.mock.calls[0];
    expect(init.method).toBe("POST");
    expect(requestHeaders(fetchImpl).get("content-type")).toBe(
      "application/json",
    );
    expect(init.body).toBe(JSON.stringify({ name: "A" }));
  });

  it("appends query parameters and omits undefined values", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse([]));
    const client = createApiClient({ baseUrl: BASE, fetchImpl });

    await client.get("/api/v1/items", {
      query: { search: "rice", page: 2, active: true, missing: undefined },
    });

    const [url] = fetchImpl.mock.calls[0];
    expect(url).toBe(`${BASE}/api/v1/items?search=rice&page=2&active=true`);
  });

  it("parses the standard error envelope into ApiRequestError", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(
      jsonResponse(
        {
          error: {
            code: "validation_error",
            message: "Request validation failed.",
            details: [
              { loc: ["query", "count"], msg: "invalid", type: "int_parsing" },
            ],
            context: null,
          },
        },
        422,
      ),
    );
    const client = createApiClient({ baseUrl: BASE, fetchImpl });

    const error = await client.get("/api/v1/status").catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiRequestError);
    const apiError = error as ApiRequestError;
    expect(apiError.code).toBe("validation_error");
    expect(apiError.status).toBe(422);
    expect(apiError.details).toHaveLength(1);
    expect(apiError.details?.[0].loc).toEqual(["query", "count"]);
  });

  it("falls back to a stable code for non-envelope error bodies", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(new Response("gateway exploded", { status: 502 }));
    const client = createApiClient({ baseUrl: BASE, fetchImpl });

    const error = await client.get("/api/v1/status").catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiRequestError);
    expect((error as ApiRequestError).code).toBe("unexpected_response");
    expect((error as ApiRequestError).status).toBe(502);
  });

  it("wraps network failures with a status of 0", async () => {
    const fetchImpl = vi
      .fn()
      .mockRejectedValue(new TypeError("Failed to fetch"));
    const client = createApiClient({ baseUrl: BASE, fetchImpl });

    const error = await client.get("/api/v1/status").catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiRequestError);
    expect((error as ApiRequestError).code).toBe("network_error");
    expect((error as ApiRequestError).status).toBe(0);
  });

  it("rethrows aborts unchanged so callers can detect cancellation", async () => {
    const fetchImpl = vi
      .fn()
      .mockRejectedValue(new DOMException("Aborted", "AbortError"));
    const client = createApiClient({ baseUrl: BASE, fetchImpl });
    const controller = new AbortController();

    const error = await client
      .get("/api/v1/status", { signal: controller.signal })
      .catch((e: unknown) => e);

    expect(error).toBeInstanceOf(DOMException);
    expect((error as DOMException).name).toBe("AbortError");
    expect(fetchImpl.mock.calls[0][1].signal).toBe(controller.signal);
  });

  it("merges defaults, injected Headers, and caller iterable headers", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse({}));
    const client = createApiClient({
      baseUrl: BASE,
      fetchImpl,
      getHeaders: () =>
        new Headers({
          Authorization: "Bearer token-123",
          "X-Precedence": "injected",
        }),
    });

    await client.get("/api/v1/status", {
      headers: [
        ["X-Request-Id", "r-1"],
        ["x-precedence", "caller"],
      ],
    });

    const headers = requestHeaders(fetchImpl);
    expect(headers.get("accept")).toBe("application/json");
    expect(headers.get("authorization")).toBe("Bearer token-123");
    expect(headers.get("x-request-id")).toBe("r-1");
    expect(headers.get("x-precedence")).toBe("caller");
  });

  it("lets caller header casing override defaults without duplication", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse({}));
    const client = createApiClient({ baseUrl: BASE, fetchImpl });

    await client.post(
      "/api/v1/things",
      { name: "A" },
      { headers: { "content-type": "application/vnd.platewise+json" } },
    );

    expect(requestHeaders(fetchImpl).get("content-type")).toBe(
      "application/vnd.platewise+json",
    );
  });

  it("returns undefined for 204 responses", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(new Response(null, { status: 204 }));
    const client = createApiClient({ baseUrl: BASE, fetchImpl });

    await expect(client.delete("/api/v1/things/1")).resolves.toBeUndefined();
  });

  it.each([200, 201, 202])(
    "returns undefined for an empty %i response",
    async (status) => {
      const fetchImpl = vi
        .fn()
        .mockResolvedValue(new Response(null, { status }));
      const client = createApiClient({ baseUrl: BASE, fetchImpl });

      await expect(client.post("/api/v1/things")).resolves.toBeUndefined();
    },
  );

  it("rejects a non-JSON success response as unexpected", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(
      new Response("created", {
        status: 200,
        headers: { "Content-Type": "text/plain" },
      }),
    );
    const client = createApiClient({ baseUrl: BASE, fetchImpl });

    const error = await client.get("/api/v1/status").catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiRequestError);
    expect((error as ApiRequestError).code).toBe("unexpected_response");
    expect((error as ApiRequestError).status).toBe(200);
  });

  it("rejects malformed JSON success without leaking SyntaxError", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(
      new Response("{not-json", {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const client = createApiClient({ baseUrl: BASE, fetchImpl });

    const error = await client.get("/api/v1/status").catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiRequestError);
    expect(error).not.toBeInstanceOf(SyntaxError);
    expect((error as ApiRequestError).code).toBe("unexpected_response");
  });
});
