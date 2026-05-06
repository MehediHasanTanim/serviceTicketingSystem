export type ProjectType = 'RENOVATION' | 'CONSTRUCTION' | 'MAINTENANCE_UPGRADE' | 'COMPLIANCE_REMEDIATION' | 'TECHNOLOGY' | 'OTHER'
export type ProjectPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type ProjectStatus = 'DRAFT' | 'PLANNED' | 'IN_PROGRESS' | 'ON_HOLD' | 'COMPLETED' | 'CANCELLED' | 'VOID'

export type SnagCategory = 'FINISHING' | 'ELECTRICAL' | 'PLUMBING' | 'HVAC' | 'CIVIL' | 'SAFETY' | 'QUALITY' | 'OTHER'
export type SnagSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type SnagStatus = 'OPEN' | 'ASSIGNED' | 'IN_PROGRESS' | 'RESOLVED' | 'VERIFIED' | 'REOPENED' | 'CANCELLED' | 'VOID'

export type TechnicalAuditStatus = 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED' | 'VOID'
export type TechnicalAuditResult = 'PASS' | 'FAIL' | 'PARTIAL' | 'OBSERVATION'

export type PaginatedResponse<T> = {
  count: number
  page?: number
  page_size?: number
  results: T[]
}

export type Project = {
  id: number
  org_id: number
  project_code: string
  title: string
  description: string
  property_id: number | null
  department_id: number | null
  project_type: ProjectType
  priority: ProjectPriority
  status: ProjectStatus
  owner_id: number | null
  manager_id: number | null
  start_date: string | null
  planned_end_date: string | null
  actual_end_date: string | null
  budget_amount: string
  actual_cost: string
  progress_percentage: number
  created_by: number
  updated_by: number
  created_at: string
  updated_at: string
}

export type ProjectListFilters = {
  q: string
  property: string
  department: string
  project_type: string
  status: string
  priority: string
  owner: string
  manager: string
  date_from: string
  date_to: string
  page: number
  page_size: number
  sort_by: string
  sort_dir: 'asc' | 'desc'
}

export type ProjectTimelineEvent = {
  id: number
  project_id: number
  event_type: string
  previous_status: ProjectStatus | null
  new_status: ProjectStatus | null
  progress_percentage: number | null
  message: string
  metadata: Record<string, unknown>
  actor_id: number | null
  created_at: string
}

export type SnaggingItem = {
  id: number
  snag_number: string
  project_id: number
  title: string
  description: string
  category: SnagCategory
  severity: SnagSeverity
  status: SnagStatus
  location_id: number | null
  room_id: number | null
  asset_id: number | null
  assigned_to: number | null
  reported_by: number
  due_at: string | null
  resolved_at: string | null
  verified_at: string | null
  created_at: string
  updated_at: string
}

export type TechnicalAudit = {
  id: number
  audit_number: string
  project_id: number
  title: string
  scope: string
  auditor_id: number | null
  status: TechnicalAuditStatus
  result: TechnicalAuditResult | null
  score: number | null
  findings_summary: string
  corrective_actions_required: boolean
  conducted_at: string | null
  completed_at: string | null
  created_by: number
  created_at: string
  updated_at: string
}

export type AuditLog = {
  id: number
  org_id: number
  property_id: number | null
  actor_user_id: number | null
  action: string
  target_type: string
  target_id: string
  metadata: Record<string, unknown>
  ip_address: string
  user_agent: string
  created_at: string
}

export type ProjectAuditLogFilters = {
  q: string
  property_id: string
  actor_user_id: string
  action: string
  target_type: string
  target_id: string
  date_from: string
  date_to: string
  page: number
  page_size: number
  sort_by: 'created_at' | 'action' | 'target_type'
  sort_dir: 'asc' | 'desc'
}

export type SnaggingListFilters = {
  q: string
  category: string
  severity: string
  status: string
  assigned_to: string
  room: string
  location: string
  due_from: string
  due_to: string
  page: number
  page_size: number
  sort_by: string
  sort_dir: 'asc' | 'desc'
}

export type TechnicalAuditListFilters = {
  q: string
  status: string
  result: string
  auditor: string
  conducted_from: string
  conducted_to: string
  page: number
  page_size: number
  sort_by: string
  sort_dir: 'asc' | 'desc'
}
