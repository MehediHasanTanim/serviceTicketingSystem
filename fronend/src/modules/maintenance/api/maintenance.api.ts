import { apiRequest } from '../../../shared/api/client'
import type {
  Asset,
  AssetFilters,
  AssetLifecycleRow,
  AuditLog,
  AuditLogFilters,
  MaintenanceLogbookEntry,
  MaintenanceOrder,
  MaintenanceAttachment,
  MaintenanceOrderFilters,
  PMSchedule,
  PaginatedResponse,
} from '../types/maintenance.types'

function authHeader(token: string) {
  return { Authorization: `Bearer ${token}` }
}

function setParam(params: URLSearchParams, key: string, value: string | number | undefined) {
  if (value === undefined || value === '' || value === null) return
  params.set(key, String(value))
}

export async function fetchMaintenanceOrders(accessToken: string, orgId: number, filters: MaintenanceOrderFilters) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  setParam(params, 'page', filters.page)
  setParam(params, 'page_size', filters.page_size)
  setParam(params, 'task_type', filters.task_type)
  setParam(params, 'status', filters.status)
  setParam(params, 'priority', filters.priority)
  setParam(params, 'asset', filters.asset)
  setParam(params, 'room', filters.room)
  setParam(params, 'property', filters.property)
  setParam(params, 'department', filters.department)
  setParam(params, 'assigned_to', filters.assigned_to)
  setParam(params, 'date_from', filters.date_from)
  setParam(params, 'date_to', filters.date_to)
  return apiRequest(`/maintenance/tasks?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<MaintenanceOrder>>
}

export async function fetchMaintenanceOrder(accessToken: string, orgId: number, id: number) {
  return apiRequest(`/maintenance/tasks/${id}?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<MaintenanceOrder>
}

export async function createMaintenanceOrder(accessToken: string, payload: Record<string, unknown>) {
  return apiRequest('/maintenance/tasks', { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<MaintenanceOrder>
}

export async function updateMaintenanceOrder(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/maintenance/tasks/${id}`, { method: 'PATCH', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<MaintenanceOrder>
}

export async function assignMaintenanceOrder(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/maintenance/tasks/${id}/assign`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<MaintenanceOrder>
}

export async function transitionMaintenanceOrder(accessToken: string, id: number, action: 'start' | 'hold' | 'complete' | 'cancel' | 'void', payload: Record<string, unknown>) {
  return apiRequest(`/maintenance/tasks/${id}/${action}`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<MaintenanceOrder>
}

export async function fetchMaintenanceLogbook(accessToken: string, orgId: number, taskId: number) {
  return apiRequest(`/maintenance/tasks/${taskId}/logbook?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<{ count: number; results: MaintenanceLogbookEntry[] }>
}

export async function createMaintenanceLogbookEntry(accessToken: string, taskId: number, payload: Record<string, unknown>) {
  return apiRequest(`/maintenance/tasks/${taskId}/logbook`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<MaintenanceLogbookEntry>
}

export async function recalculateMaintenanceCosts(accessToken: string, taskId: number, payload: Record<string, unknown>) {
  return apiRequest(`/maintenance/tasks/${taskId}/costs`, { method: 'PATCH', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<MaintenanceOrder>
}

export async function fetchPMSchedules(accessToken: string, orgId: number, filters: { page: number; page_size: number }) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  setParam(params, 'page', filters.page)
  setParam(params, 'page_size', filters.page_size)
  return apiRequest(`/maintenance/pm-schedules?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<PMSchedule>>
}

export async function createPMSchedule(accessToken: string, payload: Record<string, unknown>) {
  return apiRequest('/maintenance/pm-schedules', { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<{ id: number }>
}

export async function updatePMSchedule(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/maintenance/pm-schedules/${id}`, { method: 'PATCH', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<{ id: number }>
}

export async function runPMScheduler(accessToken: string, payload: Record<string, unknown>) {
  return apiRequest('/maintenance/pm-scheduler/run', { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<Record<string, unknown>>
}

export async function fetchAssets(accessToken: string, orgId: number, filters: AssetFilters) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  setParam(params, 'page', filters.page)
  setParam(params, 'page_size', filters.page_size)
  setParam(params, 'q', filters.q)
  setParam(params, 'status', filters.status)
  setParam(params, 'category', filters.category)
  setParam(params, 'location', filters.location)
  setParam(params, 'room', filters.room)
  setParam(params, 'department', filters.department)
  setParam(params, 'property', filters.property)
  setParam(params, 'criticality', filters.criticality)
  setParam(params, 'warranty_expiring_before', filters.warranty_expiring_before)
  return apiRequest(`/maintenance/assets?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<Asset>>
}

export async function fetchAsset(accessToken: string, orgId: number, id: number) {
  return apiRequest(`/maintenance/assets/${id}?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<Asset>
}

export async function createAsset(accessToken: string, payload: Record<string, unknown>) {
  return apiRequest('/maintenance/assets', { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<Asset>
}

export async function updateAsset(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/maintenance/assets/${id}`, { method: 'PATCH', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<Asset>
}

export async function transitionAssetStatus(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/maintenance/assets/${id}/status`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<Asset>
}

export async function fetchAssetHistory(accessToken: string, orgId: number, id: number) {
  return apiRequest(`/maintenance/assets/${id}/history?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<{ count: number; results: AssetLifecycleRow[] }>
}

export async function lookupAssetByQR(accessToken: string, orgId: number, qrCode: string) {
  return apiRequest(`/maintenance/assets/qr/${encodeURIComponent(qrCode)}?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<{ asset: Asset; current_status: string; open_maintenance_tasks: MaintenanceOrder[]; recent_logbook_entries: Array<{ id: number; entry_type: string; description: string; created_at: string }> }>
}

export async function createTaskFromQR(accessToken: string, qrCode: string, payload: Record<string, unknown>) {
  return apiRequest(`/maintenance/assets/qr/${encodeURIComponent(qrCode)}/tasks`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<MaintenanceOrder>
}

export async function fetchMaintenanceAttachments(accessToken: string, orgId: number, taskId: number) {
  return apiRequest(`/maintenance/tasks/${taskId}/attachments?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<{ count: number; results: MaintenanceAttachment[] }>
}

export async function addMaintenanceAttachment(accessToken: string, taskId: number, payload: Record<string, unknown>) {
  return apiRequest(`/maintenance/tasks/${taskId}/attachments`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<MaintenanceAttachment>
}

export async function fetchMaintenanceAuditLogs(accessToken: string, orgId: number, filters: AuditLogFilters) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  setParam(params, 'page', filters.page)
  setParam(params, 'page_size', filters.page_size)
  setParam(params, 'q', filters.q)
  setParam(params, 'property_id', filters.property_id)
  setParam(params, 'actor_user_id', filters.actor_user_id)
  setParam(params, 'action', filters.action)
  setParam(params, 'target_type', filters.target_type)
  setParam(params, 'target_id', filters.target_id)
  setParam(params, 'date_from', filters.date_from)
  setParam(params, 'date_to', filters.date_to)
  setParam(params, 'sort_by', filters.sort_by)
  setParam(params, 'sort_dir', filters.sort_dir)
  return apiRequest(`/audit-logs?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<AuditLog>>
}

export function mapTasksToCalendarItems(tasks: MaintenanceOrder[]) {
  const now = new Date().getTime()
  return tasks
    .filter((task) => task.scheduled_at || task.due_at)
    .map((task) => {
      const at = task.scheduled_at || task.due_at || new Date().toISOString()
      return {
        id: task.id,
        title: task.title,
        at,
        status: task.status,
        priority: task.priority,
        overdue: !!task.due_at && new Date(task.due_at).getTime() < now && !['COMPLETED', 'CANCELLED', 'VOID'].includes(task.status),
      }
    })
}

export const placeholderScheduleFromTask = (task: MaintenanceOrder): PMSchedule => ({
  id: task.id, asset_id: task.asset_id || 0, title: task.title, description: task.description, frequency_type: 'CUSTOM', frequency_interval: 1, next_run_at: task.scheduled_at || task.created_at, last_run_at: task.completed_at, start_date: (task.scheduled_at || task.created_at).slice(0, 10), end_date: null, priority: task.priority, is_active: task.status !== 'VOID' && task.status !== 'CANCELLED',
})
