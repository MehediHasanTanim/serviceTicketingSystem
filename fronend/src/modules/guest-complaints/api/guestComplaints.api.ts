import { apiRequest } from '../../../shared/api/client'
import type {
  ComplaintAnalyticsSummary,
  ComplaintAnalyticsTrends,
  ComplaintAuditLog,
  ComplaintFollowUp,
  ComplaintListFilters,
  ComplaintResolutionTime,
  ComplaintSatisfaction,
  GuestComplaint,
  PaginatedResponse,
} from '../types/guestComplaints.types'

function authHeader(token: string) {
  return { Authorization: `Bearer ${token}` }
}

function setParam(params: URLSearchParams, key: string, value: string | number | undefined) {
  if (value === undefined || value === '') return
  params.set(key, String(value))
}

export async function getGuestComplaints(accessToken: string, orgId: number, filters: ComplaintListFilters) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  setParam(params, 'page', filters.page)
  setParam(params, 'page_size', filters.page_size)
  setParam(params, 'q', filters.q)
  setParam(params, 'status', filters.status)
  setParam(params, 'severity', filters.severity)
  setParam(params, 'category', filters.category)
  setParam(params, 'source', filters.source)
  setParam(params, 'property', filters.property)
  setParam(params, 'department', filters.department)
  setParam(params, 'assigned_to', filters.assigned_to)
  setParam(params, 'escalated_to', filters.escalated_to)
  setParam(params, 'date_from', filters.date_from)
  setParam(params, 'date_to', filters.date_to)
  return apiRequest(`/guest-complaints?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<GuestComplaint>>
}

export async function getGuestComplaint(accessToken: string, orgId: number, id: number) {
  return apiRequest(`/guest-complaints/${id}?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<GuestComplaint>
}

export async function createGuestComplaint(accessToken: string, payload: Record<string, unknown>) {
  return apiRequest('/guest-complaints', { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<GuestComplaint>
}

export async function updateGuestComplaint(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/guest-complaints/${id}`, { method: 'PATCH', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<GuestComplaint>
}

export async function assignComplaint(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/guest-complaints/${id}/assign`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<GuestComplaint>
}

export async function complaintLifecycleAction(accessToken: string, id: number, action: 'start' | 'resolve' | 'reopen' | 'void', payload: Record<string, unknown>) {
  return apiRequest(`/guest-complaints/${id}/${action}`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<GuestComplaint>
}

export async function escalateComplaint(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/guest-complaints/${id}/escalate`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<{ status: string; result: string }>
}

export async function confirmComplaintResolution(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/guest-complaints/${id}/confirm-resolution`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<GuestComplaint>
}

export async function getComplaintFollowUps(accessToken: string, orgId: number, complaintId: number) {
  return apiRequest(`/guest-complaints/${complaintId}/follow-ups?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<{ count: number; results: ComplaintFollowUp[] }>
}

export async function createComplaintFollowUp(accessToken: string, complaintId: number, payload: Record<string, unknown>) {
  return apiRequest(`/guest-complaints/${complaintId}/follow-ups`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<{ id: number; status: string }>
}

export async function completeComplaintFollowUp(accessToken: string, followUpId: number, payload: Record<string, unknown>) {
  return apiRequest(`/guest-complaints/follow-ups/${followUpId}/complete`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<{ id: number; status: string; completed_at: string }>
}

export async function getComplaintAnalyticsSummary(accessToken: string, orgId: number, filters: Record<string, string>) {
  const params = new URLSearchParams({ org_id: String(orgId), ...filters })
  return apiRequest(`/guest-complaints/analytics/summary?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<ComplaintAnalyticsSummary>
}

export async function getComplaintAnalyticsTrends(accessToken: string, orgId: number, filters: Record<string, string>) {
  const params = new URLSearchParams({ org_id: String(orgId), ...filters })
  return apiRequest(`/guest-complaints/analytics/trends?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<ComplaintAnalyticsTrends>
}

export async function getComplaintAnalyticsResolutionTime(accessToken: string, orgId: number, filters: Record<string, string>) {
  const params = new URLSearchParams({ org_id: String(orgId), ...filters })
  return apiRequest(`/guest-complaints/analytics/resolution-time?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<ComplaintResolutionTime>
}

export async function getComplaintAnalyticsSatisfaction(accessToken: string, orgId: number, filters: Record<string, string>) {
  const params = new URLSearchParams({ org_id: String(orgId), ...filters })
  return apiRequest(`/guest-complaints/analytics/satisfaction?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<ComplaintSatisfaction>
}

export async function getComplaintAuditLogs(accessToken: string, orgId: number, filters: { action?: string; target_id?: string }) {
  const params = new URLSearchParams({ org_id: String(orgId) })
  if (filters.action) params.set('action', filters.action)
  if (filters.target_id) params.set('target_id', filters.target_id)
  return apiRequest(`/guest-complaints/audit-logs?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<{ count: number; results: ComplaintAuditLog[] }>
}
