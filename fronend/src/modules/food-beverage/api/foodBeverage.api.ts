import { apiRequest } from '../../../shared/api/client'
import type {
  BreakfastCount,
  BreakfastCountFilters,
  FBAuditFilters,
  FBAuditLog,
  FBMetricsSummary,
  FBTask,
  FBTaskFilters,
  FBTrendPoint,
  OutletReadinessFilters,
  OutletReadinessRecord,
  PaginatedResponse,
} from '../types/foodBeverage.types'

function authHeader(token: string) {
  return { Authorization: `Bearer ${token}` }
}

function setParam(params: URLSearchParams, key: string, value: string | number | undefined) {
  if (value === undefined || value === '' || value === null) return
  params.set(key, String(value))
}

export const foodBeverageApi = {
  async getBreakfastCounts(accessToken: string, orgId: number, filters: BreakfastCountFilters) {
    const p = new URLSearchParams()
    setParam(p, 'org_id', orgId); setParam(p, 'property_id', filters.property_id); setParam(p, 'outlet_id', filters.outlet_id)
    setParam(p, 'date_from', filters.date_from); setParam(p, 'date_to', filters.date_to); setParam(p, 'q', filters.q)
    setParam(p, 'sort_by', filters.sort_by); setParam(p, 'sort_dir', filters.sort_dir); setParam(p, 'page', filters.page); setParam(p, 'page_size', filters.page_size)
    return apiRequest(`/food-beverage/breakfast-counts?${p.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<BreakfastCount>>
  },
  async getBreakfastCountDetail(accessToken: string, orgId: number, id: number) {
    return apiRequest(`/food-beverage/breakfast-counts/${id}?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<BreakfastCount>
  },
  async createBreakfastCount(accessToken: string, payload: Record<string, unknown>) {
    return apiRequest('/food-beverage/breakfast-counts', { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<BreakfastCount>
  },
  async updateBreakfastCount(accessToken: string, id: number, payload: Record<string, unknown>) {
    return apiRequest(`/food-beverage/breakfast-counts/${id}`, { method: 'PATCH', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<BreakfastCount>
  },
  async getOutletReadiness(accessToken: string, orgId: number, filters: OutletReadinessFilters) {
    const p = new URLSearchParams()
    setParam(p, 'org_id', orgId); setParam(p, 'property_id', filters.property_id); setParam(p, 'outlet_id', filters.outlet_id)
    setParam(p, 'shift', filters.shift); setParam(p, 'status', filters.status); setParam(p, 'date_from', filters.date_from); setParam(p, 'date_to', filters.date_to)
    setParam(p, 'page', filters.page); setParam(p, 'page_size', filters.page_size)
    return apiRequest(`/food-beverage/outlet-readiness?${p.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<OutletReadinessRecord>>
  },
  async getOutletReadinessDetail(accessToken: string, orgId: number, id: number) {
    return apiRequest(`/food-beverage/outlet-readiness/${id}?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<OutletReadinessRecord>
  },
  async createOutletReadiness(accessToken: string, payload: Record<string, unknown>) {
    return apiRequest('/food-beverage/outlet-readiness', { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<OutletReadinessRecord>
  },
  async updateOutletReadiness(accessToken: string, id: number, payload: Record<string, unknown>) {
    return apiRequest(`/food-beverage/outlet-readiness/${id}`, { method: 'PATCH', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<OutletReadinessRecord>
  },
  async outletReadinessAction(accessToken: string, id: number, action: 'start'|'submit'|'verify'|'void', payload: Record<string, unknown>) {
    return apiRequest(`/food-beverage/outlet-readiness/${id}/${action}`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<OutletReadinessRecord>
  },
  async getFBTasks(accessToken: string, orgId: number, filters: FBTaskFilters) {
    const p = new URLSearchParams()
    setParam(p, 'org_id', orgId); setParam(p, 'property_id', filters.property_id); setParam(p, 'outlet_id', filters.outlet_id)
    setParam(p, 'task_type', filters.task_type); setParam(p, 'priority', filters.priority); setParam(p, 'status', filters.status)
    setParam(p, 'staff_id', filters.staff_id); setParam(p, 'date_from', filters.date_from); setParam(p, 'date_to', filters.date_to)
    setParam(p, 'q', filters.q); setParam(p, 'page', filters.page); setParam(p, 'page_size', filters.page_size)
    return apiRequest(`/food-beverage/tasks?${p.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<FBTask>>
  },
  async getFBTaskDetail(accessToken: string, orgId: number, id: number) {
    return apiRequest(`/food-beverage/tasks/${id}?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<FBTask>
  },
  async createFBTask(accessToken: string, payload: Record<string, unknown>) {
    return apiRequest('/food-beverage/tasks', { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<FBTask>
  },
  async updateFBTask(accessToken: string, id: number, payload: Record<string, unknown>) {
    return apiRequest(`/food-beverage/tasks/${id}`, { method: 'PATCH', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<FBTask>
  },
  async assignFBTask(accessToken: string, id: number, payload: Record<string, unknown>) {
    return apiRequest(`/food-beverage/tasks/${id}/assign`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<FBTask>
  },
  async fbTaskAction(accessToken: string, id: number, action: 'start'|'complete'|'cancel'|'void', payload: Record<string, unknown>) {
    return apiRequest(`/food-beverage/tasks/${id}/${action}`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<FBTask>
  },
  async getFBMetricsSummary(accessToken: string, orgId: number, query: URLSearchParams) {
    query.set('org_id', String(orgId))
    return apiRequest(`/food-beverage/metrics/summary?${query.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<FBMetricsSummary>
  },
  async getFBMetricsBreakfast(accessToken: string, orgId: number, query: URLSearchParams) {
    query.set('org_id', String(orgId))
    return apiRequest(`/food-beverage/metrics/breakfast?${query.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<FBTrendPoint[]>
  },
  async getFBMetricsReadiness(accessToken: string, orgId: number, query: URLSearchParams) {
    query.set('org_id', String(orgId))
    return apiRequest(`/food-beverage/metrics/outlet-readiness?${query.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<FBTrendPoint[]>
  },
  async getFBMetricsTasks(accessToken: string, orgId: number, query: URLSearchParams) {
    query.set('org_id', String(orgId))
    return apiRequest(`/food-beverage/metrics/tasks?${query.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<FBTrendPoint[]>
  },
  async getFBAuditLogs(accessToken: string, orgId: number, filters: FBAuditFilters) {
    const p = new URLSearchParams()
    setParam(p, 'org_id', orgId); setParam(p, 'date_from', filters.date_from); setParam(p, 'date_to', filters.date_to)
    setParam(p, 'actor_user_id', filters.actor_user_id); setParam(p, 'action', filters.action); setParam(p, 'target_type', filters.target_type)
    setParam(p, 'outlet_id', filters.outlet_id); setParam(p, 'task_id', filters.task_id); setParam(p, 'breakfast_count_id', filters.breakfast_count_id); setParam(p, 'readiness_id', filters.readiness_id)
    setParam(p, 'page', filters.page); setParam(p, 'page_size', filters.page_size); setParam(p, 'sort_by', filters.sort_by); setParam(p, 'sort_dir', filters.sort_dir)
    return apiRequest(`/food-beverage/audit-logs?${p.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<FBAuditLog>>
  },
}
