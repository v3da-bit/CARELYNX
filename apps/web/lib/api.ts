/**
 * Typed API client. All business logic lives in the API; this module only transports data.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export type Role = "patient" | "reviewer";

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public requestId?: string,
    public status?: number,
  ) {
    super(message);
  }
}

export async function api<T>(path: string, init: RequestInit & { role?: Role } = {}): Promise<T> {
  const { role = "patient", headers, ...rest } = init;
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...rest,
      headers: { "X-Carelynx-Role": role, ...(headers ?? {}) },
      cache: "no-store",
    });
  } catch {
    throw new ApiError("NETWORK_ERROR", "Cannot reach the CARELYNX API. Is it running?");
  }
  if (!res.ok) {
    let code = "HTTP_ERROR";
    let message = `Request failed (${res.status})`;
    let requestId: string | undefined;
    try {
      const body = await res.json();
      code = body?.error?.code ?? code;
      message = body?.error?.message ?? message;
      requestId = body?.error?.request_id;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(code, message, requestId, res.status);
  }
  return (await res.json()) as T;
}

export interface Health {
  status: "ok" | "degraded";
  database: "ok" | "unavailable";
  database_backend: string;
  inference_provider: string;
  inference_hardware_label: string;
}

export const getHealth = () => api<Health>("/health");
