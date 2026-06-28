import type {
  ApiEnvelope,
  AuditLog,
  Criterion,
  EvaluationDetail,
  LatestEvaluations,
  LoginResponse,
  PageData,
  Project,
  Subject,
  UploadedFile,
  User,
} from "./types"

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ""
const TOKEN_KEY = "trialmatch_access_token"
const USER_KEY = "trialmatch_user"

export type ApiState<T> = {
  data: T | null
  error: string | null
  loading: boolean
}

export function getStoredToken(): string | null {
  return window.localStorage.getItem(TOKEN_KEY)
}

export function getStoredUser(): User | null {
  const raw = window.localStorage.getItem(USER_KEY)
  if (raw === null) {
    return null
  }
  try {
    return JSON.parse(raw) as User
  } catch {
    window.localStorage.removeItem(USER_KEY)
    return null
  }
}

export function clearSession(): void {
  window.localStorage.removeItem(TOKEN_KEY)
  window.localStorage.removeItem(USER_KEY)
}

function storeSession(data: LoginResponse): void {
  window.localStorage.setItem(TOKEN_KEY, data.access_token)
  window.localStorage.setItem(USER_KEY, JSON.stringify(data.user))
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  const token = getStoredToken()
  const hasBody = options.body !== undefined

  if (hasBody && !headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json")
  }
  if (token !== null) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  let envelope: ApiEnvelope<T>
  try {
    envelope = (await response.json()) as ApiEnvelope<T>
  } catch {
    throw new Error(`接口响应不是 JSON：${response.status}`)
  }

  if (!response.ok || envelope.code !== 0) {
    throw new Error(envelope.message || `接口请求失败：${response.status}`)
  }

  return envelope.data
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const data = await request<LoginResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  })
  storeSession(data)
  return data
}

export async function fetchMe(): Promise<User> {
  return request<User>("/api/v1/auth/me")
}

export async function fetchProjects(): Promise<PageData<Project>> {
  return request<PageData<Project>>("/api/v1/projects?page_size=100")
}

export async function fetchProject(projectId: string): Promise<Project> {
  return request<Project>(`/api/v1/projects/${projectId}`)
}

export async function createProject(input: {
  project_no: string
  study_name: string
  indication?: string
  phase?: string
  sponsor?: string
}): Promise<{ id: string; project_no: string }> {
  return request<{ id: string; project_no: string }>("/api/v1/projects", {
    method: "POST",
    body: JSON.stringify(input),
  })
}

export async function updateProject(
  projectId: string,
  input: {
    study_name?: string
    study_short_name?: string
    indication?: string
    phase?: string
    sponsor?: string
    principal_investigator?: string
    project_manager?: string
    status?: string
    description?: string
    ai_prompt?: string
  },
): Promise<boolean> {
  return request<boolean>(`/api/v1/projects/${projectId}`, {
    method: "PUT",
    body: JSON.stringify(input),
  })
}

export async function fetchSubjects(projectId: string): Promise<PageData<Subject>> {
  return request<PageData<Subject>>(`/api/v1/projects/${projectId}/subjects?page_size=100`)
}

export async function fetchSubject(subjectId: string): Promise<Subject> {
  return request<Subject>(`/api/v1/subjects/${subjectId}`)
}

export async function createSubject(
  projectId: string,
  input: {
    subject_no: string
    site_name?: string
    gender?: string
    age?: number
    diagnosis?: string
  },
): Promise<{ id: string; subject_no: string }> {
  return request<{ id: string; subject_no: string }>(`/api/v1/projects/${projectId}/subjects`, {
    method: "POST",
    body: JSON.stringify(input),
  })
}

export async function fetchCriteria(projectId: string): Promise<Criterion[]> {
  return request<Criterion[]>(`/api/v1/projects/${projectId}/criteria`)
}

export async function createCriterion(
  projectId: string,
  input: {
    criterion_code: string
    criterion_type: "inclusion" | "exclusion"
    criterion_text: string
    ai_instruction?: string
    sort_order: number
  },
): Promise<{ id: string }> {
  return request<{ id: string }>(`/api/v1/projects/${projectId}/criteria`, {
    method: "POST",
    body: JSON.stringify(input),
  })
}

export async function fetchFiles(projectId: string, subjectId?: string): Promise<PageData<UploadedFile>> {
  const params = new URLSearchParams({ project_id: projectId, page_size: "100" })
  if (subjectId !== undefined) {
    params.set("subject_id", subjectId)
  }
  return request<PageData<UploadedFile>>(`/api/v1/files?${params.toString()}`)
}

export async function uploadProjectFile(projectId: string, file: File, fileType: string): Promise<UploadedFile> {
  const form = new FormData()
  form.set("file", file)
  form.set("file_type", fileType)
  form.set("file_scope", "project_protocol")
  return request<UploadedFile>(`/api/v1/files/projects/${projectId}/files`, {
    method: "POST",
    body: form,
  })
}

export async function uploadSubjectFile(subjectId: string, file: File, fileType: string): Promise<UploadedFile> {
  const form = new FormData()
  form.set("file", file)
  form.set("file_type", fileType)
  form.set("file_scope", "subject_data")
  return request<UploadedFile>(`/api/v1/files/subjects/${subjectId}/files`, {
    method: "POST",
    body: form,
  })
}

export async function fetchLatestEvaluations(subjectId: string): Promise<LatestEvaluations> {
  return request<LatestEvaluations>(`/api/v1/subjects/${subjectId}/evaluations/latest`)
}

export async function fetchEvaluationDetail(evaluationId: string): Promise<EvaluationDetail> {
  return request<EvaluationDetail>(`/api/v1/evaluations/${evaluationId}`)
}

export async function submitManualReview(
  evaluationId: string,
  input: {
    manual_result: string
    manual_comment?: string
    review_status: "reviewed" | "modified"
  },
): Promise<{ evaluation_id: string; review_status: string }> {
  return request<{ evaluation_id: string; review_status: string }>(
    `/api/v1/evaluations/${evaluationId}/manual-review`,
    {
      method: "PUT",
      body: JSON.stringify(input),
    },
  )
}

export async function startScreening(subjectId: string): Promise<{ id: string; run_no: string; status: string }> {
  return request<{ id: string; run_no: string; status: string }>(`/api/v1/subjects/${subjectId}/screening-runs`, {
    method: "POST",
    body: JSON.stringify({ prompt_version: "frontend-manual-run" }),
  })
}

export async function exportReport(subjectId: string): Promise<{ export_task_id: string; download_url?: string; status: string }> {
  return request<{ export_task_id: string; download_url?: string; status: string }>(
    `/api/v1/subjects/${subjectId}/export-report`,
    { method: "POST" },
  )
}

export async function fetchAuditLogs(): Promise<PageData<AuditLog>> {
  return request<PageData<AuditLog>>("/api/v1/audit-logs?page_size=50")
}

export async function fetchHealth(): Promise<{ status: string; version?: string; database?: string }> {
  const response = await fetch(`${API_BASE}/health/detailed`)
  if (!response.ok) {
    throw new Error(`健康检查失败：${response.status}`)
  }
  return (await response.json()) as { status: string; version?: string; database?: string }
}
