export type Priority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT'
export type MaintenanceTaskType = 'CORRECTIVE' | 'PREVENTIVE'
export type MaintenanceTaskStatus = 'OPEN' | 'ASSIGNED' | 'IN_PROGRESS' | 'ON_HOLD' | 'COMPLETED' | 'CANCELLED' | 'VOID'
export type AssetStatus = 'ACTIVE' | 'INACTIVE' | 'UNDER_MAINTENANCE' | 'OUT_OF_SERVICE' | 'RETIRED'
export type AssetCriticality = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type LogbookEntryType = 'DIAGNOSIS' | 'WORK_PERFORMED' | 'PART_USED' | 'LABOR' | 'NOTE' | 'COMPLETION_SUMMARY'
export type FrequencyType = 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'QUARTERLY' | 'YEARLY' | 'CUSTOM'

export type PaginatedResponse<T> = {
  count: number
  page: number
  page_size: number
  results: T[]
}

export type MaintenanceOrder = {
  id: number
  org_id: number
  task_number: string
  task_type: MaintenanceTaskType
  title: string
  description: string
  asset_id: number | null
  room_id: number | null
  property_id: number | null
  department_id: number | null
  priority: Priority
  status: MaintenanceTaskStatus
  assigned_to: number | null
  reported_by: number
  scheduled_at: string | null
  due_at: string | null
  started_at: string | null
  completed_at: string | null
  parts_total: string
  labor_total: string
  total_cost: string
  created_at: string
  updated_at: string
}

export type MaintenanceOrderFilters = {
  q: string
  task_type: string
  status: string
  priority: string
  asset: string
  room: string
  property: string
  department: string
  assigned_to: string
  date_from: string
  date_to: string
  page: number
  page_size: number
}

export type Asset = {
  id: number
  org_id: number
  asset_code: string
  qr_code: string | null
  name: string
  description: string
  category: string
  location_id: number | null
  room_id: number | null
  department_id: number | null
  property_id: number | null
  manufacturer: string
  model_number: string
  serial_number: string
  purchase_date: string | null
  warranty_expiry_date: string | null
  status: AssetStatus
  criticality: AssetCriticality
  created_at: string
  updated_at: string
}

export type AssetFilters = {
  q: string
  status: string
  category: string
  location: string
  room: string
  department: string
  property: string
  criticality: string
  warranty_expiring_before: string
  page: number
  page_size: number
}

export type AssetLifecycleRow = {
  id: number
  asset_id: number
  previous_status: AssetStatus
  new_status: AssetStatus
  changed_by: number
  changed_at: string
  reason: string
  metadata: Record<string, unknown>
}

export type PMSchedule = {
  id: number
  asset_id: number
  title: string
  description: string
  frequency_type: FrequencyType
  frequency_interval: number
  next_run_at: string
  last_run_at: string | null
  start_date: string
  end_date: string | null
  priority: Priority
  is_active: boolean
}

export type MaintenanceAttachment = {
  id: number
  file_name: string
  storage_key: string
  uploaded_by: number
  uploaded_at: string
}

export type LogbookPart = {
  id?: number
  part_name: string
  part_number: string
  quantity: string
  unit_cost: string
  total_cost: string
}

export type LogbookLabor = {
  id?: number
  technician_id: number
  hours: string
  hourly_rate: string
  total_labor_cost: string
}

export type MaintenanceLogbookEntry = {
  id: number
  maintenance_task_id: number
  asset_id: number | null
  entry_type: LogbookEntryType
  description: string
  created_by: number
  created_at: string
  parts: LogbookPart[]
  labor: LogbookLabor[]
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

export type AuditLogFilters = {
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
