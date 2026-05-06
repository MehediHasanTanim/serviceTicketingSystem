export type Grouping = 'day' | 'week' | 'month' | 'quarter'

export type ReportType =
  | 'OPERATIONAL_SUMMARY'
  | 'DEPARTMENT_PERFORMANCE'
  | 'SLA_REPORT'
  | 'COST_REPORT'
  | 'COMPLIANCE_REPORT'
  | 'ENERGY_REPORT'
  | 'CUSTOM'

export type ReportOutputFormat = 'JSON' | 'EXCEL' | 'PDF'
export type ScheduleOutputFormat = 'EXCEL' | 'PDF'
export type ScheduleFrequency = 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'QUARTERLY'
export type ReportRunStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'

export type ReportingMetricFilters = {
  org_id?: number
  date_from?: string
  date_to?: string
  property_id?: number | string
  department_id?: number | string
  module?: string
  grouping?: Grouping
}

export type ExecutiveSummary = {
  open_tasks_by_module: Record<string, number>
  completed_tasks_by_module: Record<string, number>
  overdue_items_by_module: Record<string, number>
  average_resolution_hours: number
  total_operational_cost: number
  compliance_rate: number
  guest_satisfaction_score: number
  energy_efficiency_kpi: number
}

export type DepartmentPerformance = ExecutiveSummary & {
  department_id?: number | string | null
}

export type SlaAnalytics = ExecutiveSummary & {
  sla_compliance_percent: number
}

export type CostsAnalytics = {
  total_operational_cost: number
}

export type ComplianceAnalytics = {
  compliance_rate: number
}

export type EnergyAnalytics = {
  energy_efficiency_kpi: number
}

export type ReportDefinitionListItem = {
  id: number
  report_code: string
  name: string
  report_type: ReportType
  is_active: boolean
}

export type ReportDefinitionDetail = {
  id: number
  report_code: string
  name: string
  description: string
  module_scope: string[]
  report_type: ReportType
  default_filters: Record<string, unknown>
  columns_config: Record<string, unknown> | unknown[]
  chart_config: Record<string, unknown>
  is_active: boolean
}

export type ReportDefinitionCreatePayload = {
  report_code: string
  name: string
  description?: string
  module_scope?: string[]
  report_type: ReportType
  default_filters?: Record<string, unknown>
  columns_config?: Record<string, unknown> | unknown[]
  chart_config?: Record<string, unknown>
  is_active?: boolean
}

export type ReportDefinitionUpdatePayload = Partial<Omit<ReportDefinitionCreatePayload, 'report_code'>>

export type ReportRunListItem = {
  id: number
  report_definition_id: number
  status: ReportRunStatus
  output_format: ReportOutputFormat
  created_at: string
  completed_at?: string | null
  error_message?: string | null
}

export type ReportRunDetail = {
  id: number
  status: ReportRunStatus
  filters: Record<string, unknown>
  output_format: ReportOutputFormat
  storage_key?: string | null
  error_message?: string | null
}

export type ReportRunRequestPayload = {
  report_definition_id: number
  filters: Record<string, unknown>
  output_format: ReportOutputFormat
}

export type ReportRunResponse = {
  id: number
  status: ReportRunStatus
  storage_key?: string | null
  error_message?: string | null
}

export type ReportDownloadResponse = {
  file_path: string
  size: number
}

export type ReportScheduleListItem = {
  id: number
  name: string
  frequency_type: ScheduleFrequency
  is_active: boolean
  next_run_at?: string | null
  last_run_at?: string | null
}

export type ReportScheduleDetail = {
  id: number
  name: string
  frequency_type: ScheduleFrequency
  frequency_config: Record<string, unknown>
  recipients: string[]
  output_format: ScheduleOutputFormat
  filters: Record<string, unknown>
  is_active: boolean
  next_run_at?: string | null
  last_run_at?: string | null
}

export type ReportScheduleCreatePayload = {
  report_definition_id: number
  name: string
  frequency_type: ScheduleFrequency
  frequency_config?: Record<string, unknown>
  recipients?: string[]
  output_format: ScheduleOutputFormat
  filters?: Record<string, unknown>
  is_active?: boolean
}

export type ReportScheduleUpdatePayload = Partial<Omit<ReportScheduleCreatePayload, 'report_definition_id'>>

export type ReportScheduleResponse = {
  id: number
  name?: string
  next_run_at?: string | null
  is_active?: boolean
}

export type ScheduleRunDueSummary = {
  schedules_checked: number
  reports_generated: number
  emails_sent: number
  failures: number
}

export type AuditLogRow = {
  id: number
  created_at: string
  actor_user_id?: number | null
  action: string
  target_type: string
  target_id: string
  metadata?: Record<string, unknown>
}

export type PaginatedResponse<T> = {
  count: number
  results: T[]
}
