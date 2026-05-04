export type HousekeepingTaskStatus = 'PENDING' | 'ASSIGNED' | 'IN_PROGRESS' | 'COMPLETED' | 'VERIFIED' | 'CANCELLED'
export type HousekeepingPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT'
export type RoomOccupancyStatus = 'OCCUPIED' | 'VACANT' | 'RESERVED' | 'OUT_OF_ORDER'
export type RoomHousekeepingStatus = 'CLEAN' | 'DIRTY' | 'INSPECTING' | 'READY' | 'BLOCKED'

export type RoomStatusRow = {
  id: number
  room_id: number
  occupancy_status: RoomOccupancyStatus
  housekeeping_status: RoomHousekeepingStatus
  priority: HousekeepingPriority
  updated_at: string
  updated_by: number | null
}

export type HousekeepingTaskLike = {
  id: string
  roomNumber: string
  taskType: 'CLEANING' | 'INSPECTION' | 'DEEP_CLEAN' | 'MAINTENANCE_SUPPORT' | 'TURNDOWN'
  priority: HousekeepingPriority
  status: HousekeepingTaskStatus
  assignedStaff?: string
  dueAt?: string
  overdue: boolean
  source: 'audit'
}

export type HousekeepingTaskFilters = {
  date: string
  property: string
  floor: string
  room: string
  staff: string
  priority: string
  taskType: string
  status: string
  q: string
}

export type HousekeepingKpiSummary = {
  total_tasks_created: number
  total_tasks_completed: number
  pending_tasks_count: number
  overdue_tasks_count: number
  avg_completion_minutes: number
  avg_room_turnaround_minutes: number
  sla_compliance_pct: number
}

export type HousekeepingStaffPerformance = {
  staff_id: number
  display_name: string
  tasks_completed: number
  avg_completion_minutes: number
}

export type HousekeepingTurnaround = {
  events: number
  average_minutes: number
  by_room_type?: Array<{ room_type: string; average_minutes: number; events: number }>
}

export type HousekeepingAuditLog = {
  id: number
  actor_user_id: number | null
  actor_email?: string
  action: string
  target_type: string
  target_id: string
  metadata?: Record<string, unknown>
  created_at: string
}
