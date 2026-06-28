export type ApiEnvelope<T> = {
  code: number
  message: string
  data: T
  request_id: string
}

export type PageData<T> = {
  items: T[]
  total: number
  page: number
  page_size: number
}

export type User = {
  id: string
  username: string
  display_name: string
  role: string
  email?: string | null
  status?: string
}

export type LoginResponse = {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

export type Project = {
  id: string
  project_no: string
  study_name: string
  study_short_name?: string | null
  indication?: string | null
  phase?: string | null
  sponsor?: string | null
  principal_investigator?: string | null
  project_manager?: string | null
  status: string
  description?: string | null
  ai_prompt?: string | null
  created_by: string
  created_at: string
  updated_at: string
}

export type Subject = {
  id: string
  project_id: string
  subject_no: string
  site_name?: string | null
  gender?: string | null
  age?: number | null
  birth_year?: number | null
  diagnosis?: string | null
  remark?: string | null
  material_count: number
  screening_status: string
  overall_result?: string | null
  created_at: string
  updated_at: string
}

export type Criterion = {
  id: string
  project_id: string
  criterion_code: string
  criterion_type: "inclusion" | "exclusion" | string
  criterion_text: string
  criterion_explanation?: string | null
  ai_instruction?: string | null
  required_fields?: string[] | null
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export type UploadedFile = {
  id: string
  project_id: string
  subject_id?: string | null
  file_name: string
  file_type: string
  file_scope: string
  mime_type?: string | null
  file_size?: number | null
  page_count?: number | null
  parse_status: string
  description?: string | null
  uploaded_by?: string | null
  uploaded_at: string
}

export type Citation = {
  id?: string
  file_id?: string | null
  file_name?: string | null
  file_type?: string | null
  page_no?: number | null
  chunk_id?: string | null
  quoted_text?: string | null
  extracted_fact?: string | null
  relevance_explanation?: string | null
}

export type Evaluation = {
  id: string
  criterion_id: string
  criterion_code: string
  criterion_type: string
  criterion_text: string
  ai_result: string
  confidence_score?: number | null
  ai_rationale?: string | null
  citation_count: number
  manual_result?: string | null
  manual_comment?: string | null
  review_status: string
}

export type EvaluationDetail = Evaluation & {
  run_id: string
  project_id: string
  subject_id: string
  criterion_explanation?: string | null
  citations: Citation[]
}

export type LatestEvaluations = {
  run_id: string | null
  subject: Subject | null
  project: Project | null
  summary: {
    overall_result?: string | null
    score?: number | null
    ai_advice?: string | null
    inclusion_pass_count: number
    inclusion_fail_count: number
    inclusion_insufficient_count: number
    exclusion_hit_count: number
    exclusion_not_hit_count: number
    manual_review_count: number
  } | null
  evaluations: Evaluation[]
}

export type AuditLog = {
  id: string
  project_id?: string | null
  subject_id?: string | null
  user_id?: string | null
  action_type: string
  target_type: string
  target_id: string
  before_value?: unknown
  after_value?: unknown
  created_at?: string | null
}
