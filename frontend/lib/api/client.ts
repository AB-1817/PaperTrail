/**
 * Typed API Client for PaperTrail FastAPI Backend
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface ApiResponse<T> {
  data: T | null;
  meta: Record<string, any> | null;
  error: { code: string; message: string; request_id: string } | null;
}

export interface Paper {
  id: string;
  doi?: string | null;
  title: string;
  abstract?: string | null;
  year?: number | null;
  venue?: string | null;
  open_access: boolean;
  oa_url?: string | null;
  authors: { name: string; position: number }[];
  topics?: string[];
  score?: number;
  explanation?: {
    matched_terms?: string[];
    details?: string[];
  };
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  try {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });
    const json = await res.json();
    return json;
  } catch (err: any) {
    return {
      data: null,
      meta: null,
      error: {
        code: "NETWORK_ERROR",
        message: err.message || "Failed to connect to backend",
        request_id: "",
      },
    };
  }
}

export async function searchPapers(
  query: string,
  page: number = 1,
  strategy: string = "hybrid_rrf",
  filters: { year_from?: number; year_to?: number; open_access?: boolean } = {}
): Promise<ApiResponse<Paper[]>> {
  const res = await request<Paper[]>("/api/v1/search", {
    method: "POST",
    body: JSON.stringify({
      q: query,
      page,
      per_page: 20,
      strategy,
      ...filters,
    }),
  });

  return res;
}

export async function getPaper(id: string): Promise<ApiResponse<Paper>> {
  return request<Paper>(`/api/v1/papers/${encodeURIComponent(id)}`);
}

export async function getPaperReferences(id: string): Promise<ApiResponse<any[]>> {
  return request<any[]>(`/api/v1/papers/${encodeURIComponent(id)}/references`);
}

export async function getPersonalizedRecommendations(
  token: string
): Promise<ApiResponse<Paper[]>> {
  return request<Paper[]>("/api/v1/recommendations/personalized", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

// ── Ingestion ────────────────────────────────────────────────────────────────

export type IngestionProvider = "openalex" | "arxiv" | "semantic_scholar" | "crossref";

export interface IngestionJob {
  job_id: string;
  status: "pending" | "running" | "completed" | "failed";
  papers_found?: number;
  papers_inserted?: number;
  papers_updated?: number;
  errors?: string[];
  started_at?: string | null;
  completed_at?: string | null;
}

export async function triggerIngestion(
  query: string,
  provider: IngestionProvider = "openalex",
  limit: number = 20,
  token: string
): Promise<ApiResponse<{ job_id: string; status: string }>> {
  return request<{ job_id: string; status: string }>("/api/v1/ingestion/trigger", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ query, provider, limit }),
  });
}

export async function getIngestionJob(
  jobId: string,
  token: string
): Promise<ApiResponse<IngestionJob>> {
  return request<IngestionJob>(`/api/v1/ingestion/jobs/${jobId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}
