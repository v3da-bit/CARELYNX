/* eslint-disable @typescript-eslint/no-explicit-any */
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
  let token: string | null = null;
  if (typeof window !== "undefined") {
    try {
      token = localStorage.getItem("carelynx_auth_token");
    } catch {
      /* ignore */
    }
  }
  const authHeaders: Record<string, string> = {};
  if (token) {
    authHeaders["Authorization"] = `Bearer ${token}`;
  }
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...rest,
      headers: { "X-Carelynx-Role": role, ...authHeaders, ...(headers ?? {}) },
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

export interface CaseCreated {
  id: string;
}

export const createCase = () => api<CaseCreated>("/cases", { method: "POST" });

export interface DocumentUpload {
  id: string;
  case_id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
}

export const uploadDocument = async (caseId: string, file: File): Promise<DocumentUpload> => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("case_id", caseId);
  
  const headers: Record<string, string> = { "X-Carelynx-Role": "patient" };
  if (typeof window !== "undefined") {
    try {
      const token = localStorage.getItem("carelynx_auth_token");
      if (token) headers["Authorization"] = `Bearer ${token}`;
    } catch {
      // ignore
    }
  }

  // Note: Cannot use our 'api' helper easily here because of FormData content-type handling.
  // fetch will automatically set the correct multipart/form-data boundary.
  const res = await fetch(`${API_BASE}/documents`, {
    method: "POST",
    body: formData,
    headers,
  });
  if (!res.ok) {
    let msg = `Upload failed (${res.status})`;
    try {
      const body = await res.json();
      msg = body?.error?.message || body?.detail || msg;
    } catch {
      // ignore
    }
    throw new Error(msg);
  }
  return res.json();
};

export const processDocument = (docId: string) => api<{ status: string }>(`/documents/${docId}/process`, { method: "POST" });

export interface DocumentResponse {
  id: string;
  filename: string;
  processing_status: string;
}

export interface CaseOut {
  id: string;
  status: string;
  documents: DocumentResponse[];
  counts: Record<string, unknown>;
  created_at?: string;
}

export const getCase = (caseId: string) => api<CaseOut>(`/cases/${caseId}`);

export interface FactResponse {
  id: string;
  fact_type: string;
  value: Record<string, unknown>;
  status: string;
  confidence: number | null;
  status_reasons: string[];
}

export const getCaseFacts = (caseId: string) => api<FactResponse[]>(`/cases/${caseId}/facts`);
export const getFact = (factId: string) => api<FactResponse>(`/facts/${factId}`);

export interface CarePlanItem extends FactResponse {
  display: { title: string; subtitle: string | null; date: string | null };
  translation_status: "source" | "translated" | "pending_review" | "unavailable";
}

export interface CarePlan {
  case_id: string;
  language: string;
  sections: Record<string, CarePlanItem[]>;
}

export const getCarePlan = (caseId: string, lang: string) =>
  api<CarePlan>(`/cases/${caseId}/care-plan?lang=${lang}`);

export type TranslatedText = { 
  title?: string; 
  subtitle?: string | null; 
  date?: string | null; 
  [key: string]: any;
};

/** Server-translated text for VERIFIED facts only (others stay in English until reviewed). */
export const translateCase = async (caseId: string, lang: string): Promise<Record<string, TranslatedText>> => {
  const plan = await getCarePlan(caseId, lang);
  const out: Record<string, TranslatedText> = {};
  for (const item of Object.values(plan.sections).flat()) {
    if (item.translation_status === "translated") out[item.id] = item.display;
  }
  return out;
};

export interface EvidenceResponse {
  id: string;
  document_id: string;
  page_number: number;
  snippet: string | null;
}

export const getFactEvidence = (factId: string) => api<EvidenceResponse[]>(`/facts/${factId}/evidence`);

export interface ReviewCaseResponse {
  id: string;
  case_id: string;
  reason: string;
  reason_code: string;
  severity: string;
  status: string;
  fact_ids: string[];
  conflict_id: string | null;
  document_id: string | null;
  recommended_action: string;
  decision: string | null;
  resolved_by: string | null;
  created_at: string;
  resolved_at: string | null;
}

export const getOpenReviews = () => api<ReviewCaseResponse[]>("/reviews", { headers: { "X-Carelynx-Role": "reviewer" }});
export const getReview = (id: string) => api<ReviewCaseResponse>(`/reviews/${id}`, { headers: { "X-Carelynx-Role": "reviewer" }});

export interface ResolveReviewRequest {
  decision: "APPROVE" | "REJECT" | "SELECT_SOURCE" | "CORRECT_VALUE";
  resolution_notes: string;
  reviewer_id: string;
  winning_fact_id?: string;
  corrected_value?: Record<string, unknown>;
}

export const resolveReview = (id: string, req: ResolveReviewRequest) =>
  api<ReviewCaseResponse>(`/reviews/${id}/resolve`, {
    method: "POST",
    body: JSON.stringify(req),
    headers: { "Content-Type": "application/json", "X-Carelynx-Role": "reviewer" }
  });

export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  created_at: string;
}

export interface AuthResponse {
  token: string;
  user: UserProfile;
}

export const registerUser = async (email: string, password: string, fullName?: string): Promise<AuthResponse> => {
  const res = await api<AuthResponse>("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  if (typeof window !== "undefined") {
    localStorage.setItem("carelynx_auth_token", res.token);
  }
  return res;
};

export const loginUser = async (email: string, password: string): Promise<AuthResponse> => {
  const res = await api<AuthResponse>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (typeof window !== "undefined") {
    localStorage.setItem("carelynx_auth_token", res.token);
  }
  return res;
};

export const logoutUser = () => {
  if (typeof window !== "undefined") {
    localStorage.removeItem("carelynx_auth_token");
  }
};

export const getMe = () => api<UserProfile>("/auth/me");
export const getUserCases = () => api<CaseOut[]>("/cases");

