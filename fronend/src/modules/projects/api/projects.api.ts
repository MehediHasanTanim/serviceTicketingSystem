import { apiRequest } from '../../../shared/api/client'
import type {
  AuditLog,
  PaginatedResponse,
  Project,
  ProjectAuditLogFilters,
  ProjectListFilters,
  ProjectTimelineEvent,
  SnaggingListFilters,
  SnaggingItem,
  TechnicalAuditListFilters,
  TechnicalAudit,
} from '../types/projects.types'

function authHeader(token: string) {
  return { Authorization: `Bearer ${token}` }
}

function setParam(params: URLSearchParams, key: string, value: string | number | undefined) {
  if (value === undefined || value === '' || value === null) return
  params.set(key, String(value))
}

export async function fetchProjects(accessToken: string, orgId: number, filters: ProjectListFilters) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  setParam(params, 'page', filters.page)
  setParam(params, 'page_size', filters.page_size)
  setParam(params, 'q', filters.q)
  setParam(params, 'property', filters.property)
  setParam(params, 'department', filters.department)
  setParam(params, 'project_type', filters.project_type)
  setParam(params, 'status', filters.status)
  setParam(params, 'priority', filters.priority)
  setParam(params, 'owner', filters.owner)
  setParam(params, 'manager', filters.manager)
  setParam(params, 'date_from', filters.date_from)
  setParam(params, 'date_to', filters.date_to)
  setParam(params, 'sort_by', filters.sort_by)
  setParam(params, 'sort_dir', filters.sort_dir)
  return apiRequest(`/projects?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<Project>>
}

export async function fetchProjectDetail(accessToken: string, orgId: number, id: number) {
  return apiRequest(`/projects/${id}?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<Project>
}

export async function createProject(accessToken: string, payload: Record<string, unknown>) {
  return apiRequest('/projects', { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<Project>
}

export async function updateProject(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/projects/${id}`, { method: 'PATCH', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<Project>
}

export async function updateProjectStatus(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/projects/${id}/status`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<Project>
}

export async function updateProjectProgress(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/projects/${id}/progress`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<Project>
}

export async function fetchProjectTimeline(accessToken: string, orgId: number, projectId: number) {
  return apiRequest(`/projects/${projectId}/timeline?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<{ count: number; results: ProjectTimelineEvent[] }>
}

export async function fetchProjectSnaggingItems(accessToken: string, orgId: number, projectId: number, filters: SnaggingListFilters) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  setParam(params, 'q', filters.q)
  setParam(params, 'category', filters.category)
  setParam(params, 'severity', filters.severity)
  setParam(params, 'status', filters.status)
  setParam(params, 'assigned_to', filters.assigned_to)
  setParam(params, 'room', filters.room)
  setParam(params, 'location', filters.location)
  setParam(params, 'due_from', filters.due_from)
  setParam(params, 'due_to', filters.due_to)
  setParam(params, 'page', filters.page)
  setParam(params, 'page_size', filters.page_size)
  setParam(params, 'sort_by', filters.sort_by)
  setParam(params, 'sort_dir', filters.sort_dir)
  return apiRequest(`/projects/${projectId}/snagging-items?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<{ count: number; page?: number; page_size?: number; results: SnaggingItem[] }>
}

export async function createSnaggingItem(accessToken: string, projectId: number, payload: Record<string, unknown>) {
  return apiRequest(`/projects/${projectId}/snagging-items`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<SnaggingItem>
}

export async function fetchSnaggingItemDetail(accessToken: string, orgId: number, snagId: number) {
  return apiRequest(`/projects/snagging-items/${snagId}?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<SnaggingItem>
}

export async function updateSnaggingItem(accessToken: string, snagId: number, payload: Record<string, unknown>) {
  return apiRequest(`/projects/snagging-items/${snagId}`, { method: 'PATCH', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<SnaggingItem>
}

export async function snaggingItemAction(accessToken: string, snagId: number, action: 'assign' | 'start' | 'resolve' | 'verify' | 'reopen' | 'cancel' | 'void', payload: Record<string, unknown>) {
  return apiRequest(`/projects/snagging-items/${snagId}/${action}`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<SnaggingItem>
}

export async function fetchTechnicalAudits(accessToken: string, orgId: number, projectId: number, filters: TechnicalAuditListFilters) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  setParam(params, 'q', filters.q)
  setParam(params, 'status', filters.status)
  setParam(params, 'result', filters.result)
  setParam(params, 'auditor', filters.auditor)
  setParam(params, 'conducted_from', filters.conducted_from)
  setParam(params, 'conducted_to', filters.conducted_to)
  setParam(params, 'page', filters.page)
  setParam(params, 'page_size', filters.page_size)
  setParam(params, 'sort_by', filters.sort_by)
  setParam(params, 'sort_dir', filters.sort_dir)
  return apiRequest(`/projects/${projectId}/technical-audits?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<{ count: number; page?: number; page_size?: number; results: TechnicalAudit[] }>
}

export async function createTechnicalAudit(accessToken: string, projectId: number, payload: Record<string, unknown>) {
  return apiRequest(`/projects/${projectId}/technical-audits`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<TechnicalAudit>
}

export async function fetchTechnicalAuditDetail(accessToken: string, orgId: number, auditId: number) {
  return apiRequest(`/projects/technical-audits/${auditId}?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<TechnicalAudit>
}

export async function updateTechnicalAudit(accessToken: string, auditId: number, payload: Record<string, unknown>) {
  return apiRequest(`/projects/technical-audits/${auditId}`, { method: 'PATCH', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<TechnicalAudit>
}

export async function technicalAuditAction(accessToken: string, auditId: number, action: 'start' | 'complete' | 'cancel' | 'void', payload: Record<string, unknown>) {
  return apiRequest(`/projects/technical-audits/${auditId}/${action}`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<TechnicalAudit>
}

export async function fetchProjectAuditLogs(accessToken: string, orgId: number, filters: ProjectAuditLogFilters) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  setParam(params, 'q', filters.q)
  setParam(params, 'property_id', filters.property_id)
  setParam(params, 'actor_user_id', filters.actor_user_id)
  setParam(params, 'action', filters.action)
  setParam(params, 'target_type', filters.target_type)
  setParam(params, 'target_id', filters.target_id)
  setParam(params, 'date_from', filters.date_from)
  setParam(params, 'date_to', filters.date_to)
  setParam(params, 'page', filters.page)
  setParam(params, 'page_size', filters.page_size)
  setParam(params, 'sort_by', filters.sort_by)
  setParam(params, 'sort_dir', filters.sort_dir)
  return apiRequest(`/audit-logs?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<AuditLog>>
}
