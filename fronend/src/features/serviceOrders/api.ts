import { apiRequest } from '../../shared/api/client'
import type {
  PaginatedResponse,
  ServiceOrder,
  ServiceOrderAttachment,
  ServiceOrderFilters,
  ServiceOrderRemark,
} from './types'

function authHeader(token: string) {
  return { Authorization: `Bearer ${token}` }
}

export async function fetchServiceOrders(accessToken: string, orgId: number, filters: ServiceOrderFilters) {
  const params = new URLSearchParams()
  params.set('org_id', String(orgId))
  params.set('page', String(filters.page))
  params.set('page_size', String(filters.page_size))
  params.set('sort_by', filters.sort_by)
  params.set('sort_dir', filters.sort_dir)
  if (filters.q.trim()) params.set('q', filters.q.trim())
  if (filters.status) params.set('status', filters.status)
  if (filters.priority) params.set('priority', filters.priority)
  if (filters.type) params.set('type', filters.type)
  if (filters.assigned_to) params.set('assigned_to', filters.assigned_to)
  if (filters.customer_id) params.set('customer_id', filters.customer_id)
  if (filters.date_from) params.set('date_from', filters.date_from)
  if (filters.date_to) params.set('date_to', filters.date_to)

  return apiRequest(`/service-orders?${params.toString()}`, {
    method: 'GET',
    headers: authHeader(accessToken),
  }) as Promise<PaginatedResponse<ServiceOrder>>
}

export async function fetchServiceOrder(accessToken: string, orgId: number, id: number) {
  return apiRequest(`/service-orders/${id}?org_id=${orgId}`, {
    method: 'GET',
    headers: authHeader(accessToken),
  }) as Promise<ServiceOrder>
}

export async function createServiceOrder(accessToken: string, payload: Record<string, unknown>) {
  return apiRequest('/service-orders', {
    method: 'POST',
    headers: authHeader(accessToken),
    body: JSON.stringify(payload),
  }) as Promise<ServiceOrder>
}

export async function updateServiceOrder(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/service-orders/${id}`, {
    method: 'PATCH',
    headers: authHeader(accessToken),
    body: JSON.stringify(payload),
  }) as Promise<ServiceOrder>
}

export async function transitionServiceOrder(
  accessToken: string,
  id: number,
  endpoint: 'start' | 'hold' | 'complete' | 'defer' | 'void',
  payload: Record<string, unknown>,
) {
  return apiRequest(`/service-orders/${id}/${endpoint}`, {
    method: 'POST',
    headers: authHeader(accessToken),
    body: JSON.stringify(payload),
  }) as Promise<ServiceOrder>
}

export async function assignServiceOrder(accessToken: string, id: number, payload: Record<string, unknown>, reassign = false) {
  return apiRequest(`/service-orders/${id}/${reassign ? 'reassign' : 'assign'}`, {
    method: 'POST',
    headers: authHeader(accessToken),
    body: JSON.stringify(payload),
  }) as Promise<ServiceOrder>
}

export async function addRemark(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/service-orders/${id}/remarks`, {
    method: 'POST',
    headers: authHeader(accessToken),
    body: JSON.stringify(payload),
  }) as Promise<ServiceOrderRemark>
}

export async function fetchRemarks(accessToken: string, orgId: number, id: number) {
  return apiRequest(`/service-orders/${id}/remarks?org_id=${orgId}`, {
    method: 'GET',
    headers: authHeader(accessToken),
  }) as Promise<{ count: number; results: ServiceOrderRemark[] }>
}

export async function addAttachment(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/service-orders/${id}/attachments`, {
    method: 'POST',
    headers: authHeader(accessToken),
    body: JSON.stringify(payload),
  }) as Promise<ServiceOrderAttachment>
}

export async function fetchAttachments(accessToken: string, orgId: number, id: number) {
  return apiRequest(`/service-orders/${id}/attachments?org_id=${orgId}`, {
    method: 'GET',
    headers: authHeader(accessToken),
  }) as Promise<{ count: number; results: ServiceOrderAttachment[] }>
}

export async function deleteAttachment(accessToken: string, id: number, attachmentId: number, orgId: number) {
  return apiRequest(`/service-orders/${id}/attachments/${attachmentId}?org_id=${orgId}`, {
    method: 'DELETE',
    headers: authHeader(accessToken),
  })
}

export async function updateCosts(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/service-orders/${id}/costs`, {
    method: 'PATCH',
    headers: authHeader(accessToken),
    body: JSON.stringify(payload),
  }) as Promise<ServiceOrder>
}

export async function fetchServiceOrderAuditLogs(accessToken: string, orgId: number, orderId: number) {
  const params = new URLSearchParams()
  params.set('org_id', String(orgId))
  params.set('target_type', 'service_order')
  params.set('target_id', String(orderId))
  params.set('sort_by', 'created_at')
  params.set('sort_dir', 'desc')
  params.set('page', '1')
  params.set('page_size', '50')
  return apiRequest(`/audit-logs?${params.toString()}`, {
    method: 'GET',
    headers: authHeader(accessToken),
  }) as Promise<{ count: number; results: Array<{ id: number; actor_user_id: number | null; action: string; created_at: string; metadata?: Record<string, unknown> }> }>
}
