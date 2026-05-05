export type PaginatedResponse<T> = {
  count: number
  results: T[]
}

export type InspectionResponseValue = 'PASS' | 'FAIL' | 'NA'
export type InspectionRunStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED' | 'VOID'
export type InspectionRunResult = 'PASS' | 'FAIL' | 'PARTIAL' | 'NOT_APPLICABLE' | ''

export type InspectionChecklistItem = {
  id?: number
  question: string
  description: string
  response_type: 'PASS_FAIL_NA'
  is_required: boolean
  weight: string
  sort_order: number
  non_compliance_trigger: boolean
}

export type InspectionChecklistSection = {
  id?: number
  title: string
  description: string
  sort_order: number
  weight: string
  items: InspectionChecklistItem[]
}

export type InspectionTemplate = {
  id: number
  template_code: string
  name: string
  description: string
  category: string
  property_id: number | null
  department_id: number | null
  is_active: boolean
  version: number
  sections: InspectionChecklistSection[]
  created_at: string
  updated_at: string
}

export type InspectionTemplateFilters = {
  q: string
  category: string
  department: string
  property: string
  is_active: string
  page: number
  page_size: number
}

export type InspectionRun = {
  id: number
  inspection_number: string
  template_id: number
  property_id: number | null
  department_id: number | null
  location_id: number | null
  room_id: number | null
  asset_id: number | null
  assigned_to: number | null
  inspected_by: number | null
  status: InspectionRunStatus
  result: InspectionRunResult
  final_score: string
  notes: string
  started_at: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
}

export type InspectionRunFilters = {
  template_id: string
  status: string
  result: string
  property: string
  department: string
  location: string
  room: string
  asset: string
  assigned_to: string
  inspected_by: string
  page: number
  page_size: number
}

export type InspectionResponseRow = {
  id: number
  inspection_run_id: number
  checklist_item_id: number
  response: InspectionResponseValue
  score: string
  comment: string
  evidence_attachment_id: number | null
  responded_by: number
  responded_at: string
}

export type InspectionRunHistoryRow = {
  id: number
  action: string
  actor_id: number | null
  metadata: Record<string, unknown>
  created_at: string
}

export type InspectionReportSummary = {
  total_inspections: number
  completed_inspections: number
  passed_inspections: number
  failed_inspections: number
  average_score: number
  non_compliance_count: number
}

export type InspectionTrendRow = {
  period: string
  total: number
  average_score: number
  pass_count: number
  fail_count: number
}

export type InspectionNonComplianceReport = {
  by_item: Array<{ checklist_item_id: number; question: string; fail_count: number }>
  by_location: Array<{ key: string; fail_count: number }>
  inspector_performance: Array<{ inspector_id: number; inspections: number; average_score: number; fail_rate: number }>
}

export type InspectionAlert = {
  id: number
  inspection_run_id: number
  checklist_item_id: number | null
  alert_type: string
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  message: string
  assigned_to: number | null
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED'
  created_at: string
  resolved_at: string | null
}

export type InspectionAuditLogFilters = {
  q: string
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

export type AuditLogRow = {
  id: number
  actor_user_id: number | null
  action: string
  target_type: string
  target_id: string
  metadata: Record<string, unknown>
  created_at: string
}
