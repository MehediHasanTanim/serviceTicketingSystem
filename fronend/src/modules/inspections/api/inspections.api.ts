import { apiRequest } from '../../../shared/api/client'
import type {
  AuditLogRow,
  InspectionAlert,
  InspectionAuditLogFilters,
  InspectionNonComplianceReport,
  InspectionReportSummary,
  InspectionRun,
  InspectionRunFilters,
  InspectionRunHistoryRow,
  InspectionTemplate,
  InspectionTemplateFilters,
  InspectionTrendRow,
  PaginatedResponse,
} from '../types/inspections.types'

function authHeader(token: string) {
  return { Authorization: `Bearer ${token}` }
}

function setParam(params: URLSearchParams, key: string, value: string | number | undefined) {
  if (value === undefined || value === '' || value === null) return
  params.set(key, String(value))
}

export async function fetchInspectionTemplates(accessToken: string, orgId: number, filters: InspectionTemplateFilters) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  setParam(params, 'q', filters.q)
  setParam(params, 'category', filters.category)
  setParam(params, 'department', filters.department)
  setParam(params, 'property', filters.property)
  setParam(params, 'is_active', filters.is_active)
  return apiRequest(`/inspections/templates?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<InspectionTemplate>>
}

export async function fetchInspectionTemplateDetail(accessToken: string, orgId: number, id: number) {
  return apiRequest(`/inspections/templates/${id}?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<InspectionTemplate>
}

export async function createInspectionTemplate(accessToken: string, payload: Record<string, unknown>) {
  return apiRequest('/inspections/templates', { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<InspectionTemplate>
}

export async function updateInspectionTemplate(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/inspections/templates/${id}`, { method: 'PATCH', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<InspectionTemplate>
}

export async function activateInspectionTemplate(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/inspections/templates/${id}/activate`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<InspectionTemplate>
}

export async function deactivateInspectionTemplate(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/inspections/templates/${id}/deactivate`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<InspectionTemplate>
}

export async function fetchInspectionRuns(accessToken: string, orgId: number, filters: InspectionRunFilters) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  setParam(params, 'template_id', filters.template_id)
  setParam(params, 'status', filters.status)
  setParam(params, 'result', filters.result)
  setParam(params, 'property', filters.property)
  setParam(params, 'department', filters.department)
  setParam(params, 'location', filters.location)
  setParam(params, 'room', filters.room)
  setParam(params, 'asset', filters.asset)
  setParam(params, 'assigned_to', filters.assigned_to)
  setParam(params, 'inspected_by', filters.inspected_by)
  return apiRequest(`/inspections/runs?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<InspectionRun>>
}

export async function fetchInspectionRunDetail(accessToken: string, orgId: number, id: number) {
  return apiRequest(`/inspections/runs/${id}?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<InspectionRun>
}

export async function fetchInspectionRunHistory(accessToken: string, orgId: number, id: number) {
  return apiRequest(`/inspections/runs/${id}/history?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<{ count: number; results: InspectionRunHistoryRow[] }>
}

export async function createInspectionRun(accessToken: string, payload: Record<string, unknown>) {
  return apiRequest('/inspections/runs', { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<InspectionRun>
}

export async function startInspectionRun(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/inspections/runs/${id}/start`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<InspectionRun>
}

export async function submitInspectionResponse(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/inspections/runs/${id}/responses`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<any>
}

export async function updateInspectionResponse(accessToken: string, runId: number, responseId: number, payload: Record<string, unknown>) {
  return apiRequest(`/inspections/runs/${runId}/responses/${responseId}`, { method: 'PATCH', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<any>
}

export async function completeInspectionRun(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/inspections/runs/${id}/complete`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<InspectionRun>
}

export async function cancelInspectionRun(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/inspections/runs/${id}/cancel`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<InspectionRun>
}

export async function voidInspectionRun(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/inspections/runs/${id}/void`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<InspectionRun>
}

export async function fetchInspectionReportSummary(accessToken: string, orgId: number) {
  return apiRequest(`/inspections/reports/summary?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<InspectionReportSummary>
}

export async function fetchInspectionReportTrends(accessToken: string, orgId: number, groupBy: string) {
  return apiRequest(`/inspections/reports/trends?org_id=${orgId}&group_by=${groupBy}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<{ results: InspectionTrendRow[] }>
}

export async function fetchInspectionReportNonCompliance(accessToken: string, orgId: number) {
  return apiRequest(`/inspections/reports/non-compliance?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<InspectionNonComplianceReport>
}

export async function fetchNonComplianceAlerts(accessToken: string, orgId: number) {
  return apiRequest(`/inspections/non-compliance-alerts?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<InspectionAlert>>
}

export async function acknowledgeNonComplianceAlert(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/inspections/non-compliance-alerts/${id}/acknowledge`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<{ id: number; status: string }>
}

export async function resolveNonComplianceAlert(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/inspections/non-compliance-alerts/${id}/resolve`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<{ id: number; status: string }>
}

export async function fetchInspectionAuditLogs(accessToken: string, orgId: number, filters: InspectionAuditLogFilters) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  setParam(params, 'q', filters.q)
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
  return apiRequest(`/audit-logs?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<AuditLogRow>>
}
