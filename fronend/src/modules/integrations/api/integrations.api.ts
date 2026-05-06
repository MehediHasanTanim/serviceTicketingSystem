import { apiRequest } from '../../../shared/api/client'
import type { IntegrationAlert, IntegrationAuditLog, IntegrationAuditLogFilters, IntegrationHealthOverview, IntegrationJob, IntegrationJobsFilters, IntegrationProvider, IntegrationProviderPayload, IntegrationProvidersFilters, PaginatedResponse } from '../types/integrations.types'

function authHeader(token: string) {
  return { Authorization: `Bearer ${token}` }
}

function setParam(params: URLSearchParams, key: string, value: string | number | undefined) {
  if (value === undefined || value === '' || value === null) return
  params.set(key, String(value))
}

const safePaginated = <T>(raw: any): PaginatedResponse<T> => ({ count: Number(raw?.count || 0), results: Array.isArray(raw?.results) ? raw.results : [] })

export async function fetchIntegrationProviders(accessToken: string, orgId: number, filters: IntegrationProvidersFilters) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  setParam(params, 'q', filters.q)
  setParam(params, 'provider_type', filters.provider_type)
  setParam(params, 'status', filters.status)
  setParam(params, 'auth_type', filters.auth_type)
  setParam(params, 'date_from', filters.date_from)
  setParam(params, 'date_to', filters.date_to)
  setParam(params, 'sort_by', filters.sort_by)
  setParam(params, 'sort_dir', filters.sort_dir)
  setParam(params, 'page', filters.page)
  setParam(params, 'page_size', filters.page_size)
  const raw = await apiRequest(`/integrations/providers?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) })
  return safePaginated<IntegrationProvider>(raw)
}

export const fetchIntegrationProviderDetail = (accessToken: string, id: number) => apiRequest(`/integrations/providers/${id}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<IntegrationProvider>
export const createIntegrationProvider = (accessToken: string, payload: IntegrationProviderPayload) => apiRequest('/integrations/providers', { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<IntegrationProvider>
export const updateIntegrationProvider = (accessToken: string, id: number, payload: Partial<IntegrationProviderPayload>) => apiRequest(`/integrations/providers/${id}`, { method: 'PATCH', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<IntegrationProvider>
export const activateIntegrationProvider = (accessToken: string, id: number, payload: { org_id: number }) => apiRequest(`/integrations/providers/${id}/activate`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) })
export const deactivateIntegrationProvider = (accessToken: string, id: number, payload: { org_id: number }) => apiRequest(`/integrations/providers/${id}/deactivate`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) })
export const runProviderHealthCheck = (accessToken: string, id: number, payload: { org_id: number }) => apiRequest(`/integrations/providers/${id}/health-check`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) })
export const fetchProviderHealth = (accessToken: string, id: number) => apiRequest(`/integrations/providers/${id}/health`, { method: 'GET', headers: authHeader(accessToken) })

export async function fetchIntegrationsHealth(accessToken: string, orgId: number) {
  return apiRequest(`/integrations/health?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) })
}

export async function fetchIntegrationMetricsSummary(accessToken: string, orgId: number) {
  const raw = await apiRequest(`/integrations/metrics/summary?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) })
  return {
    total_providers: Number(raw?.total_providers || 0),
    active_providers: Number(raw?.active_providers || 0),
    providers_in_error: Number(raw?.providers_in_error || 0),
    total_jobs: Number(raw?.total_jobs || 0),
    successful_jobs: Number(raw?.successful_jobs || 0),
    failed_jobs: Number(raw?.failed_jobs || 0),
    retrying_jobs: Number(raw?.retrying_jobs || 0),
    dead_letter_jobs: Number(raw?.dead_letter_jobs || 0),
    success_rate: Number.isFinite(Number(raw?.success_rate)) ? Number(raw?.success_rate) : 0,
    avg_duration_ms: Number.isFinite(Number(raw?.avg_duration_ms)) ? Number(raw?.avg_duration_ms) : 0,
  } as IntegrationHealthOverview
}

export const fetchIntegrationFailureMetrics = (accessToken: string, orgId: number) => apiRequest(`/integrations/metrics/failures?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) })

export async function fetchIntegrationJobs(accessToken: string, orgId: number, filters: IntegrationJobsFilters) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  Object.entries(filters).forEach(([k, v]) => setParam(params, k, v as string | number))
  const raw = await apiRequest(`/integrations/jobs?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) })
  return safePaginated<IntegrationJob>(raw)
}

export const fetchIntegrationJobDetail = (accessToken: string, id: number, orgId: number) => apiRequest(`/integrations/jobs/${id}?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<IntegrationJob>
export const retryIntegrationJob = (accessToken: string, id: number, payload: { org_id: number }) => apiRequest(`/integrations/jobs/${id}/retry`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) })
export const moveIntegrationJobToDeadLetter = (accessToken: string, id: number, payload: { org_id: number }) => apiRequest(`/integrations/jobs/${id}/dead-letter`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) })

export async function fetchDeadLetterJobs(accessToken: string, orgId: number, page = 1, page_size = 20) {
  const raw = await apiRequest(`/integrations/jobs/dead-letter?org_id=${orgId}&page=${page}&page_size=${page_size}`, { method: 'GET', headers: authHeader(accessToken) })
  return safePaginated<IntegrationJob>(raw)
}

export async function fetchIntegrationAuditLogs(accessToken: string, orgId: number, filters: IntegrationAuditLogFilters) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  setParam(params, 'q', filters.q)
  setParam(params, 'actor_user_id', filters.actor_user_id)
  setParam(params, 'action', filters.action)
  setParam(params, 'target_type', filters.target_type)
  setParam(params, 'target_id', filters.target_id)
  setParam(params, 'date_from', filters.date_from)
  setParam(params, 'date_to', filters.date_to)
  setParam(params, 'sort_by', filters.sort_by)
  setParam(params, 'sort_dir', filters.sort_dir)
  setParam(params, 'page', filters.page)
  setParam(params, 'page_size', filters.page_size)
  const raw = await apiRequest(`/integrations/audit-logs?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) })
  return safePaginated<IntegrationAuditLog>(raw)
}

export async function fetchIntegrationAlerts(accessToken: string, orgId: number, query: Record<string, unknown> = {}) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  Object.entries(query).forEach(([k, v]) => setParam(params, k, v as string | number))
  const raw = await apiRequest(`/integrations/alerts?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) })
  return safePaginated<IntegrationAlert>(raw)
}

export const acknowledgeIntegrationAlert = (accessToken: string, id: string, payload: { org_id: number; note?: string }) => apiRequest(`/integrations/alerts/${encodeURIComponent(id)}/acknowledge`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) })
export const resolveIntegrationAlert = (accessToken: string, id: string, payload: { org_id: number; note?: string }) => apiRequest(`/integrations/alerts/${encodeURIComponent(id)}/resolve`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) })
