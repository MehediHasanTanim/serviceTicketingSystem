export type PaginatedResponse<T> = {
  count: number
  page?: number
  page_size?: number
  results: T[]
}

export type ComplianceRequirementStatus = 'ACTIVE' | 'INACTIVE' | 'ARCHIVED'
export type CompliancePriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type FrequencyType = 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'QUARTERLY' | 'YEARLY' | 'CUSTOM'

export type ComplianceChecklistItem = {
  id?: number
  title: string
  description: string
  is_required: boolean
  evidence_required: boolean
  sort_order: number
}

export type ComplianceRequirement = {
  id: number
  requirement_code: string
  title: string
  description: string
  category: string
  regulation_reference: string
  property_id: number | null
  department_id: number | null
  owner_id: number | null
  frequency_type: FrequencyType
  frequency_interval: number
  priority: CompliancePriority
  status: ComplianceRequirementStatus
  effective_date: string | null
  expiry_date: string | null
  next_run_at: string | null
  checklist_items: ComplianceChecklistItem[]
  updated_at: string
}

export type ComplianceRequirementFilters = {
  q: string
  category: string
  property: string
  department: string
  owner: string
  priority: string
  status: string
  page: number
  page_size: number
}

export type ComplianceCheckStatus = 'PENDING' | 'COMPLIANT' | 'NON_COMPLIANT' | 'WAIVED' | 'OVERDUE' | string

export type ComplianceCheck = {
  id: number
  requirement_id: number
  due_at: string | null
  status: ComplianceCheckStatus
  assigned_to: number | null
  completed_by: number | null
  completed_at: string | null
  evidence_attachment_id: number | null
  notes: string
  next_run_at: string | null
  created_at: string
  updated_at: string
}

export type ComplianceCheckFilters = {
  requirement_id: string
  status: string
  property: string
  department: string
  owner: string
  assigned_to: string
  priority: string
  category: string
  page: number
  page_size: number
}

export type RiskStatus = 'OPEN' | 'MITIGATING' | 'MONITORING' | 'ACCEPTED' | 'CLOSED' | 'VOID'

export type RiskRegistryItem = {
  id: number
  risk_code: string
  title: string
  description: string
  category: string
  property_id: number | null
  department_id: number | null
  owner_id: number | null
  likelihood: number
  impact: number
  inherent_score: number
  residual_score: number
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string
  status: RiskStatus
  identified_at: string
  reviewed_at: string | null
  due_at: string | null
  updated_at: string
}

export type RiskFilters = {
  q: string
  risk_level: string
  status: string
  category: string
  property: string
  department: string
  owner: string
  due_from: string
  due_to: string
  page: number
  page_size: number
}

export type RiskMitigation = {
  id: number
  title: string
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED' | 'OVERDUE' | string
  due_at: string | null
  completed_at: string | null
  effectiveness_score: number | null
  assigned_to: number | null
}

export type LegalRecord = {
  id: number
  record_code: string
  record_type: 'LEGAL' | 'CONTRACT' | 'LICENSE' | 'PERMIT' | 'INSURANCE' | 'AUDIT' | string
  status: 'ACTIVE' | 'EXPIRED' | 'RENEWAL_DUE' | 'ARCHIVED' | 'VOID' | string
  expiry_date: string | null
  renewal_due_at: string | null
}

export type LegalRecordDetail = LegalRecord & {
  title?: string
  description?: string
  property_id?: number | null
  department_id?: number | null
  owner_id?: number | null
  vendor_name?: string
  effective_date?: string | null
  attachment_id?: number | null
  notes?: string
}

export type LegalRecordFilters = {
  q: string
  type: string
  status: string
  property: string
  department: string
  owner: string
  expiry_from: string
  expiry_to: string
  page: number
  page_size: number
}

export type AuditRecord = {
  id: number
  audit_code: string
  result: 'PASS' | 'FAIL' | 'PARTIAL' | 'OBSERVATION' | string
  score: string | number | null
  corrective_actions_required: boolean
}

export type AuditRecordDetail = AuditRecord & {
  title?: string
  scope?: string
  auditor?: string
  property_id?: number | null
  department_id?: number | null
  audit_date?: string | null
  attachment_id?: number | null
  related_risk_id?: number | null
  related_check_id?: number | null
  findings_summary: string
}

export type DashboardSummary = {
  total_requirements: number
  compliant_checks: number
  non_compliant_checks: number
  overdue_checks: number
  compliance_rate: number
  open_risks: number
  critical_risks: number
  overdue_mitigations: number
  expiring_contracts: number
  audit_findings: number
}

export type ComplianceStatusBreakdown = Array<{ key: string; compliant: number; non_compliant: number; overdue: number }>
export type RiskSummaryBreakdown = Array<{ risk_level: string; total: number }>
export type LegalExpiryTimeline = Array<{ date: string; expiring: number }>

export type RiskComplianceAlert = {
  id: number
  alert_type: string
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string
  entity_type: string
  entity_id: string
  message: string
  assigned_to: number | null
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED' | string
  created_at: string
  acknowledged_at: string | null
  resolved_at: string | null
}

export type RiskComplianceAuditLogFilters = {
  q: string
  actor_user_id: string
  action: string
  target_type: string
  target_id: string
  date_from: string
  date_to: string
  requirement: string
  risk: string
  legal_record: string
  audit_record: string
  page: number
  page_size: number
  sort_by: 'created_at' | 'action' | 'target_type'
  sort_dir: 'asc' | 'desc'
}

export type RiskComplianceAuditLog = {
  id: number
  actor_user_id: number | null
  action: string
  target_type: string
  target_id: string
  metadata: Record<string, unknown>
  created_at: string
}

export type ApprovalTrailEntry = {
  approver: string
  decision: 'APPROVED' | 'REJECTED' | 'PENDING'
  timestamp: string
  comment: string
  status: string
}
