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
  
  // Note: Cannot use our 'api' helper easily here because of FormData content-type handling.
  // fetch will automatically set the correct multipart/form-data boundary.
  const res = await fetch(`${API_BASE}/documents`, {
    method: "POST",
    body: formData,
    headers: { "X-Carelynx-Role": "patient" },
  });
  if (!res.ok) throw new Error("Upload failed");
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

export interface TranslatedFact {
  id: string;
  translated_value: Record<string, unknown>;
}

export const translateCase = (caseId: string, lang: string) => 
  api<{ translated_facts: TranslatedFact[] }>(`/cases/${caseId}/translate?target_lang=${lang}`, { method: "POST" });

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
  decision: "approve" | "reject" | "edit";
  resolution_notes?: string;
  reviewer_id: string;
  winning_fact_id?: string;
}

export const resolveReview = (id: string, req: ResolveReviewRequest) => 
  api<ReviewCaseResponse>(`/reviews/${id}/resolve`, { 
    method: "POST", 
    body: JSON.stringify(req),
    headers: { "Content-Type": "application/json", "X-Carelynx-Role": "reviewer" }
  });
