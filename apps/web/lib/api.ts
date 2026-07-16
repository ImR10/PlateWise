export type ApiStatus = {
  service: string;
  status: "ok";
  environment: string;
};

export type ApiStatusResult =
  | { connected: true; data: ApiStatus }
  | { connected: false; message: string };

const serverApiUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

export async function getApiStatus(): Promise<ApiStatusResult> {
  try {
    const response = await fetch(`${serverApiUrl}/api/v1/status`, {
      cache: "no-store",
    });
    if (!response.ok) {
      return { connected: false, message: `API returned ${response.status}` };
    }
    return { connected: true, data: (await response.json()) as ApiStatus };
  } catch {
    return { connected: false, message: "The API is not reachable yet." };
  }
}
