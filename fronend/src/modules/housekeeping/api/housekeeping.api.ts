import { apiRequest } from '../../../shared/api/client'
import type {
  HousekeepingAuditLog,
  HousekeepingKpiSummary,
  HousekeepingStaffPerformance,
  HousekeepingTaskStatus,
  HousekeepingTaskLike,
  HousekeepingTaskFilters,
  HousekeepingTurnaround,
  RoomStatusRow,
} from '../types/housekeeping.types'

function authHeader(token: string) {
  return { Authorization: `Bearer ${token}` }
}

export async function fetchRoomStatuses(accessToken: string, propertyId?: number) {
  const params = new URLSearchParams()
  if (propertyId) params.set('property_id', String(propertyId))
  const path = `/pms/room-status${params.toString() ? `?${params.toString()}` : ''}`
  const res = await apiRequest(path, { method: 'GET', headers: authHeader(accessToken) }) as { success: boolean; data: { results: RoomStatusRow[] } }
  return res.data.results || []
}

export async function updateRoomStatus(accessToken: string, payload: Record<string, unknown>) {
  const res = await apiRequest('/housekeeping/room-status', {
    method: 'POST',
    headers: authHeader(accessToken),
    body: JSON.stringify(payload),
  }) as { data: RoomStatusRow }
  return res.data
}

export async function assignHousekeepingBatch(accessToken: string, payload: Record<string, unknown>) {
  return apiRequest('/housekeeping/tasks/assign', {
    method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload),
  }) as Promise<{ data: { assigned_tasks: number } }>
}

export async function reassignOverdueBatch(accessToken: string, payload: Record<string, unknown>) {
  return apiRequest('/housekeeping/tasks/reassign-overdue', {
    method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload),
  }) as Promise<{ data: { reassigned: number } }>
}

export async function fetchHousekeepingKpiSummary(accessToken: string, params: URLSearchParams) {
  const res = await apiRequest(`/housekeeping/kpi/summary?${params.toString()}`, {
    method: 'GET', headers: authHeader(accessToken),
  }) as { data: HousekeepingKpiSummary }
  return res.data
}

export async function fetchHousekeepingKpiStaff(accessToken: string, params: URLSearchParams) {
  const res = await apiRequest(`/housekeeping/kpi/staff-performance?${params.toString()}`, {
    method: 'GET', headers: authHeader(accessToken),
  }) as { data: { results: HousekeepingStaffPerformance[] } }
  return res.data.results || []
}

export async function fetchHousekeepingKpiTurnaround(accessToken: string, params: URLSearchParams) {
  const res = await apiRequest(`/housekeeping/kpi/room-turnaround?${params.toString()}`, {
    method: 'GET', headers: authHeader(accessToken),
  }) as { data: HousekeepingTurnaround }
  return res.data
}

export async function fetchHousekeepingAuditLogs(accessToken: string, params: URLSearchParams) {
  return apiRequest(`/audit-logs?${params.toString()}`, {
    method: 'GET', headers: authHeader(accessToken),
  }) as Promise<{ count: number; results: HousekeepingAuditLog[] }>
}

export async function fetchHousekeepingTasks(accessToken: string, orgId: number, filters: HousekeepingTaskFilters) {
  const params = new URLSearchParams()
  params.set('org_id', String(orgId))
  params.set('page', '1')
  params.set('page_size', '200')
  params.set('sort_by', 'updated_at')
  params.set('sort_dir', 'desc')
  if (filters.property) params.set('property_id', filters.property)
  if (filters.floor) params.set('floor_id', filters.floor)
  if (filters.room) params.set('room_id', filters.room)
  if (filters.staff) params.set('assigned_to', filters.staff)
  if (filters.priority) params.set('priority', filters.priority)
  if (filters.taskType) params.set('task_type', filters.taskType)
  if (filters.status && filters.status !== 'VERIFIED') params.set('status', filters.status)
  if (filters.date) params.set('date_from', `${filters.date}T00:00:00Z`)
  if (filters.date) params.set('date_to', `${filters.date}T23:59:59Z`)
  if (filters.q.trim()) params.set('q', filters.q.trim())

  const res = await apiRequest(`/housekeeping/tasks?${params.toString()}`, {
    method: 'GET',
    headers: authHeader(accessToken),
  }) as {
    results: Array<{
      id: number
      room_id: number
      task_type: HousekeepingTaskLike['taskType']
      priority: HousekeepingTaskLike['priority']
      status: 'PENDING' | 'ASSIGNED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED'
      assigned_to: number | null
      due_at?: string
      notes?: string
    }>
  }
  const tasks = (res.results || []).map((row) => {
    const status: HousekeepingTaskStatus =
      row.status === 'COMPLETED' && (row.notes || '').includes('[verified]') ? 'VERIFIED' : row.status
    const dueAt = row.due_at
    return {
      id: String(row.id),
      roomNumber: String(row.room_id),
      taskType: row.task_type || 'CLEANING',
      priority: row.priority || 'MEDIUM',
      status,
      assignedStaff: row.assigned_to ? `#${row.assigned_to}` : undefined,
      dueAt,
      overdue: !!dueAt && new Date(dueAt).getTime() < Date.now() && !['COMPLETED', 'VERIFIED', 'CANCELLED'].includes(status),
      source: 'audit' as const,
    }
  })
  return tasks
}

export async function fetchHousekeepingTaskDetail(accessToken: string, taskId: number, orgId: number) {
  const res = await apiRequest(`/housekeeping/tasks/${taskId}?org_id=${orgId}`, {
    method: 'GET',
    headers: authHeader(accessToken),
  }) as { data: any }
  return res.data
}

export async function transitionHousekeepingTask(
  accessToken: string,
  taskId: number,
  action: 'start' | 'complete' | 'verify' | 'cancel' | 'reopen',
  payload: Record<string, unknown>,
) {
  const res = await apiRequest(`/housekeeping/tasks/${taskId}/${action}`, {
    method: 'POST',
    headers: authHeader(accessToken),
    body: JSON.stringify(payload),
  }) as { data: any }
  return res.data
}
