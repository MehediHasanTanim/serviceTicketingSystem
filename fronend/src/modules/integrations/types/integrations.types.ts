export type PaginatedResponse<T> = {
  count: number
  results: T[]
}

export type IntegrationProviderType = 'PMS' | 'ACCOUNTING' | 'BAS_IOT' | 'EMAIL' | 'SMS' | 'OTHER'
export type IntegrationStatus = 'ACTIVE' | 'INACTIVE' | 'ERROR' | 'ARCHIVED'
export type IntegrationAuthType = 'NONE' | 'API_KEY' | 'BASIC' | 'BEARER_TOKEN' | 'OAUTH2' | 'CUSTOM'

export type IntegrationProvider = {
  id: number
  provider_code: string
  name: string
  provider_type: IntegrationProviderType | string
  status: IntegrationStatus | string
  auth_type: IntegrationAuthType | string
  base_url?: string
  credentials_secret_ref?: string
  timeout_seconds?: number
  retry_policy?: Record<string, unknown> | string
  config?: Record<string, unknown> | string
  last_health_check?: string | null
  last_success?: string | null
  last_failure?: string | null
  updated_at?: string
}

export type IntegrationProvidersFilters = {
  q: string
  provider_type: string
  status: string
  auth_type: string
  date_from: string
  date_to: string
  page: number
  page_size: number
  sort_by: string
  sort_dir: 'asc' | 'desc'
}

export type IntegrationProviderPayload = {
  org_id: number
  provider_code: string
  name: string
  provider_type: string
  status: string
  base_url?: string
  auth_type: string
  credentials_secret_ref?: string
  timeout_seconds?: number
  retry_policy?: Record<string, unknown>
  config?: Record<string, unknown>
}

export type IntegrationHealthOverview = {
  total_providers: number
  active_providers: number
  providers_in_error: number
  total_jobs: number
  successful_jobs: number
  failed_jobs: number
  retrying_jobs: number
  dead_letter_jobs: number
  success_rate: number
  avg_duration_ms: number
}

export type IntegrationJobStatus = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'RETRYING' | 'DEAD_LETTER'

export type IntegrationJob = {
  id: number
  correlation_id: string
  provider_id?: number
  provider_code?: string
  provider_name?: string
  job_type?: string
  direction?: string
  status: IntegrationJobStatus | string
  source_entity_type?: string
  source_entity_id?: string
  target_entity_type?: string
  target_entity_id?: string
  retry_count?: number
  next_retry_at?: string | null
  started_at?: string | null
  completed_at?: string | null
  request_payload?: Record<string, unknown> | string | null
  response_payload?: Record<string, unknown> | string | null
  error_code?: string | null
  error_message?: string | null
  attempts?: Array<{ at: string; status: string; error_message?: string | null; retry_count?: number }>
  created_at?: string
}

export type IntegrationJobsFilters = {
  provider: string
  job_type: string
  direction: string
  status: string
  source_entity_type: string
  target_entity_type: string
  date_from: string
  date_to: string
  correlation_id: string
  page: number
  page_size: number
}

export type IntegrationAlert = {
  id: string
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  provider: string
  alert_type: string
  message: string
  related_job?: string
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED'
  created_at: string
}

export type IntegrationAuditLog = {
  id: number
  actor_user_id?: number | null
  action: string
  target_type: string
  target_id: string
  metadata: Record<string, unknown>
  created_at: string
}

export type IntegrationAuditLogFilters = {
  q: string
  actor_user_id: string
  action: string
  target_type: string
  target_id: string
  provider: string
  job: string
  date_from: string
  date_to: string
  page: number
  page_size: number
  sort_by: string
  sort_dir: 'asc' | 'desc'
}
