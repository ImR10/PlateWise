/**
 * Minimal HTTP client for the PlateWise API.
 *
 * This is integration plumbing only: no page is wired to the backend yet, and
 * state stays in the existing context providers. Future endpoint modules build
 * on `apiClient` (or `createApiClient` in tests) instead of calling `fetch`
 * directly, so error parsing, base-URL resolution, and auth headers live in
 * exactly one place.
 *
 * Errors: every failure throws `ApiRequestError`. Responses using the standard
 * envelope (`{ error: { code, message, ... } }`) keep their machine-readable
 * code; anything else gets a stable fallback code. Branch on `code`, never on
 * `message`.
 */
import type { components } from "./schema.gen";

export type ApiErrorEnvelope = components["schemas"]["ApiErrorResponse"];
export type ApiErrorInfo = components["schemas"]["ErrorInfo"];
export type ApiValidationIssue = components["schemas"]["ValidationIssue"];

/** Base URL precedence: explicit option > VITE_API_URL > local API default. */
const DEFAULT_BASE_URL: string =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiRequestError extends Error {
  /** Machine-readable error code (from the envelope, or a client fallback). */
  readonly code: string;
  /** HTTP status; 0 when the request never produced a response. */
  readonly status: number;
  readonly details: ApiValidationIssue[] | null;
  readonly context: Record<string, unknown> | null;

  constructor(
    code: string,
    message: string,
    status: number,
    details: ApiValidationIssue[] | null = null,
    context: Record<string, unknown> | null = null,
  ) {
    super(message);
    this.name = "ApiRequestError";
    this.code = code;
    this.status = status;
    this.details = details;
    this.context = context;
  }
}

export interface ApiClientOptions {
  baseUrl?: string;
  /**
   * Extra headers resolved per request — the seam where authenticated
   * headers plug in later without touching call sites.
   */
  getHeaders?: () => HeadersInit;
  /** Injectable fetch for tests. */
  fetchImpl?: typeof fetch;
}

export interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  /** JSON-serialized request body. */
  body?: unknown;
  /** Pass an AbortSignal to support cancellation. */
  signal?: AbortSignal;
  headers?: HeadersInit;
  /** Query parameters; `undefined` values are omitted. */
  query?: Record<string, string | number | boolean | undefined>;
}

function isErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  if (typeof value !== "object" || value === null || !("error" in value)) {
    return false;
  }
  const error = (value as { error: unknown }).error;
  return (
    typeof error === "object" &&
    error !== null &&
    typeof (error as { code?: unknown }).code === "string" &&
    typeof (error as { message?: unknown }).message === "string"
  );
}

function buildUrl(
  baseUrl: string,
  path: string,
  query?: RequestOptions["query"],
): string {
  const url = new URL(path, baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined) {
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

async function parseError(response: Response): Promise<ApiRequestError> {
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    // Non-JSON error body; fall through to the generic error below.
  }
  if (isErrorEnvelope(body)) {
    const { code, message, details, context } = body.error;
    return new ApiRequestError(
      code,
      message,
      response.status,
      details ?? null,
      (context as Record<string, unknown> | null | undefined) ?? null,
    );
  }
  return new ApiRequestError(
    "unexpected_response",
    `API request failed with status ${response.status}.`,
    response.status,
  );
}

function applyHeaders(target: Headers, source?: HeadersInit): void {
  if (source === undefined) {
    return;
  }
  new Headers(source).forEach((value, name) => target.set(name, value));
}

async function parseSuccess<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  const body = await response.text();
  if (body.length === 0) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type")?.toLowerCase();
  if (contentType === undefined || !contentType.includes("json")) {
    throw new ApiRequestError(
      "unexpected_response",
      `API returned a non-JSON success response with status ${response.status}.`,
      response.status,
    );
  }

  try {
    return JSON.parse(body) as T;
  } catch {
    throw new ApiRequestError(
      "unexpected_response",
      `API returned malformed JSON with status ${response.status}.`,
      response.status,
    );
  }
}

export interface ApiClient {
  request: <T>(path: string, options?: RequestOptions) => Promise<T>;
  get: <T>(
    path: string,
    options?: Omit<RequestOptions, "method" | "body">,
  ) => Promise<T>;
  post: <T>(
    path: string,
    body?: unknown,
    options?: Omit<RequestOptions, "method" | "body">,
  ) => Promise<T>;
  put: <T>(
    path: string,
    body?: unknown,
    options?: Omit<RequestOptions, "method" | "body">,
  ) => Promise<T>;
  patch: <T>(
    path: string,
    body?: unknown,
    options?: Omit<RequestOptions, "method" | "body">,
  ) => Promise<T>;
  delete: <T>(
    path: string,
    options?: Omit<RequestOptions, "method" | "body">,
  ) => Promise<T>;
}

export function createApiClient(options: ApiClientOptions = {}): ApiClient {
  const baseUrl = options.baseUrl ?? DEFAULT_BASE_URL;
  const fetchImpl = options.fetchImpl ?? fetch;

  async function request<T>(
    path: string,
    { method = "GET", body, signal, headers, query }: RequestOptions = {},
  ): Promise<T> {
    const requestHeaders = new Headers({ Accept: "application/json" });
    if (body !== undefined) {
      requestHeaders.set("Content-Type", "application/json");
    }
    applyHeaders(requestHeaders, options.getHeaders?.());
    applyHeaders(requestHeaders, headers);

    let response: Response;
    try {
      response = await fetchImpl(buildUrl(baseUrl, path, query), {
        method,
        headers: requestHeaders,
        body: body !== undefined ? JSON.stringify(body) : undefined,
        signal,
      });
    } catch (cause) {
      // Cancellation is a caller decision, not an API failure.
      if (cause instanceof DOMException && cause.name === "AbortError") {
        throw cause;
      }
      throw new ApiRequestError(
        "network_error",
        "The API is not reachable.",
        0,
      );
    }

    if (!response.ok) {
      throw await parseError(response);
    }
    return parseSuccess<T>(response);
  }

  return {
    request,
    get: (path, opts) => request(path, { ...opts, method: "GET" }),
    post: (path, body, opts) =>
      request(path, { ...opts, method: "POST", body }),
    put: (path, body, opts) => request(path, { ...opts, method: "PUT", body }),
    patch: (path, body, opts) =>
      request(path, { ...opts, method: "PATCH", body }),
    delete: (path, opts) => request(path, { ...opts, method: "DELETE" }),
  };
}

/** Shared client instance for application code. */
export const apiClient = createApiClient();
