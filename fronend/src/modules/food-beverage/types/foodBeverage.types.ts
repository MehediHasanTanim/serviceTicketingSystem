export type PaginatedResponse<T> = { count: number; results: T[] }

export type BreakfastCount = {
  id: number
  service_date: string
  property_id: number
  outlet_id: number
  expected_guest_count: number
  actual_guest_count: number
  in_house_guest_count: number
  complimentary_count: number
  paid_count: number
  no_show_count: number
  notes?: string
  recorded_by?: number | null
  updated_at: string
}

export type BreakfastCountFilters = {
  property_id: string
  outlet_id: string
  date_from: string
  date_to: string
  q: string
  sort_by: string
  sort_dir: 'asc' | 'desc'
  page: number
  page_size: number
}

export type OutletReadinessStatus = 'PENDING' | 'IN_PROGRESS' | 'READY' | 'NOT_READY' | 'VERIFIED' | 'VOID'
export type OutletReadinessShift = 'BREAKFAST' | 'LUNCH' | 'DINNER' | 'ALL_DAY' | 'OTHER'
export type ChecklistCategory = 'STAFFING' | 'CLEANLINESS' | 'EQUIPMENT' | 'INVENTORY' | 'SAFETY' | 'MENU_AVAILABILITY' | 'SERVICE_SETUP'
export type ChecklistResult = 'PASS' | 'FAIL' | 'N/A'

export type OutletReadinessItem = {
  id: number
  name: string
  category: ChecklistCategory
  is_required: boolean
  result?: ChecklistResult
  comment?: string
  completed_by?: number | null
  completed_at?: string | null
}

export type OutletReadinessRecord = {
  id: number
  readiness_date: string
  property_id: number
  outlet_id: number
  shift: OutletReadinessShift
  status: OutletReadinessStatus
  checklist_score: number
  verified_by?: number | null
  verified_at?: string | null
  updated_at: string
  checklist_items?: OutletReadinessItem[]
}

export type OutletReadinessFilters = {
  property_id: string
  outlet_id: string
  shift: string
  status: string
  date_from: string
  date_to: string
  page: number
  page_size: number
}

export type FBTaskStatus = 'PENDING' | 'ASSIGNED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED' | 'VOID'
export type FBTaskType = 'BREAKFAST_PREP' | 'OUTLET_SETUP' | 'INVENTORY_CHECK' | 'CLEANING' | 'SERVICE_SUPPORT' | 'ISSUE_RESOLUTION' | 'OTHER'

export type FBTask = {
  id: number
  task_number: string
  property_id?: number | null
  outlet_id?: number | null
  title: string
  task_type: FBTaskType
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT'
  status: FBTaskStatus
  assigned_to?: number | null
  due_at?: string | null
  started_at?: string | null
  completed_at?: string | null
  updated_at: string
}

export type FBTaskFilters = {
  property_id: string
  outlet_id: string
  task_type: string
  priority: string
  status: string
  staff_id: string
  date_from: string
  date_to: string
  q: string
  page: number
  page_size: number
}

export type FBMetricsSummary = {
  expected_breakfast_count: number
  actual_breakfast_count: number
  variance_count: number
  variance_percentage: number
  complimentary_count: number
  paid_count: number
  no_show_count: number
  outlet_ready_count: number
  outlet_not_ready_count: number
  average_readiness_score: number
  total_tasks: number
  completed_tasks: number
  overdue_tasks: number
  average_task_completion_time: number
}

export type FBTrendPoint = { date: string; value: number; label?: string; status?: string; staff?: string }

export type FBAuditLog = {
  id: number
  created_at: string
  actor_user_id?: number | null
  action: string
  target_type: string
  target_id: string
  metadata?: Record<string, unknown>
}

export type FBAuditFilters = {
  date_from: string
  date_to: string
  actor_user_id: string
  action: string
  target_type: string
  outlet_id: string
  task_id: string
  breakfast_count_id: string
  readiness_id: string
  page: number
  page_size: number
  sort_by: string
  sort_dir: 'asc' | 'desc'
}
