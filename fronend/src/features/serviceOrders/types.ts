export type ServiceOrderStatus =
  | 'OPEN'
  | 'ASSIGNED'
  | 'IN_PROGRESS'
  | 'ON_HOLD'
  | 'DEFERRED'
  | 'COMPLETED'
  | 'VOID'

export type ServiceOrderPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT'
export type ServiceOrderType = 'INSTALLATION' | 'REPAIR' | 'MAINTENANCE' | 'INSPECTION' | 'OTHER'

export type ServiceOrder = {
  id: number
  org_id: number
  ticket_number: string
  title: string
  description: string
  customer_id: number
  asset_id: number | null
  created_by: number
  assigned_to: number | null
  priority: ServiceOrderPriority
  type: ServiceOrderType
  status: ServiceOrderStatus
  due_date: string | null
  scheduled_at: string | null
  completed_at: string | null
  estimated_cost: string
  parts_cost: string
  labor_cost: string
  compensation_cost: string
  total_cost: string
  version: number
  created_at: string
  updated_at: string
}

export type PaginatedResponse<T> = {
  count: number
  page: number
  page_size: number
  results: T[]
}

export type ServiceOrderFilters = {
  q: string
  status: string
  priority: string
  type: string
  assigned_to: string
  customer_id: string
  date_from: string
  date_to: string
  page: number
  page_size: number
  sort_by: string
  sort_dir: 'asc' | 'desc'
}

export type ServiceOrderRemark = {
  id: number
  text: string
  author: number
  is_internal: boolean
  created_at: string
}

export type ServiceOrderAttachment = {
  id: number
  file_name: string
  storage_key: string
  uploaded_by: number
  uploaded_at: string
}

export type TimelineItem = {
  id: string
  kind: string
  actor: string
  at: string
  summary: string
  note?: string
}
