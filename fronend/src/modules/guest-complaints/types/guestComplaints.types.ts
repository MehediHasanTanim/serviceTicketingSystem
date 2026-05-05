export type ComplaintSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type ComplaintStatus = 'NEW' | 'TRIAGED' | 'ASSIGNED' | 'IN_PROGRESS' | 'ESCALATED' | 'RESOLVED' | 'CONFIRMED' | 'REOPENED' | 'CLOSED' | 'VOID'
export type ComplaintCategory = 'ROOM_CLEANLINESS' | 'MAINTENANCE' | 'NOISE' | 'STAFF_BEHAVIOR' | 'BILLING' | 'FOOD_BEVERAGE' | 'CHECK_IN_CHECK_OUT' | 'SAFETY_SECURITY' | 'OTHER'
export type ComplaintSource = 'FRONT_DESK' | 'GUEST_PORTAL' | 'PHONE' | 'EMAIL' | 'STAFF' | 'PMS' | 'OTHER'

export type GuestComplaint = {
  id: number
  complaint_number: string
  org_id: number
  guest_id: number | null
  guest_name: string
  guest_contact: string
  property_id: number
  room_id: number | null
  department_id: number | null
  category: ComplaintCategory
  severity: ComplaintSeverity
  status: ComplaintStatus
  title: string
  description: string
  source: ComplaintSource
  vip_guest: boolean
  reported_at: string | null
  shift: 'MORNING' | 'AFTERNOON' | 'NIGHT' | ''
  assigned_to: number | null
  escalated_to: number | null
  due_at: string | null
  resolved_at: string | null
  confirmed_at: string | null
  satisfaction_score: string | null
  satisfaction_comment: string
  created_by: number
  updated_by: number
  created_at: string
  updated_at: string
}

export type ComplaintListFilters = {
  q: string
  status: string
  severity: string
  category: string
  source: string
  property: string
  department: string
  assigned_to: string
  escalated_to: string
  date_from: string
  date_to: string
  page: number
  page_size: number
}

export type PaginatedResponse<T> = {
  count: number
  page?: number
  page_size?: number
  results: T[]
}

export type ComplaintFollowUp = {
  id: number
  complaint_id: number
  follow_up_type: string
  scheduled_at: string
  completed_at: string | null
  assigned_to: number | null
  notes: string
  status: 'PENDING' | 'COMPLETED' | 'CANCELLED' | 'MISSED'
  created_by: number
  created_at: string
  updated_at: string
}

export type ComplaintAlert = {
  complaint: GuestComplaint
  reason: 'CRITICAL' | 'OVERDUE' | 'ESCALATED' | 'REOPENED' | 'LOW_SATISFACTION' | 'FOLLOW_UP_MISSED'
  triggered_at: string
}

export type ComplaintAnalyticsSummary = {
  total_complaints: number
  open_complaints: number
  resolved_complaints: number
  escalated_complaints: number
  reopened_complaints: number
  sla_compliance_percentage: number
  complaints_by_category: Array<{ category: string; count: number }>
  complaints_by_severity: Array<{ severity: string; count: number }>
}

export type ComplaintAnalyticsTrends = { results: Array<{ period: string; count: number }> }
export type ComplaintResolutionTime = { average_resolution_time_hours: number; resolved_count: number }
export type ComplaintSatisfaction = { average_satisfaction_score: number; low_satisfaction_count: number; responses_count: number }

export type ComplaintAuditLog = {
  id: number
  actor_id: number | null
  action: string
  entity_type: string
  entity_id: string
  metadata: Record<string, unknown>
  ip_address: string
  user_agent: string
  created_at: string
}
