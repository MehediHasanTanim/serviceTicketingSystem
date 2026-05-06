import { apiRequest } from '../../../shared/api/client'
import type { AuditLog, CAPEXRequest, Contract, PaginatedResponse, PurchaseOrder, Supplier, ApprovalRecord } from '../types/corporate.types'

const auth = (token: string) => ({ Authorization: `Bearer ${token}` })

function withQuery(path: string, query: Record<string, string | number | undefined | null>) {
  const params = new URLSearchParams()
  Object.entries(query).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') params.set(k, String(v))
  })
  const q = params.toString()
  return q ? `${path}?${q}` : path
}

export const corporateApi = {
  getSuppliers: (token: string, query: Record<string, unknown>) => apiRequest(withQuery('/corporate/suppliers', query as any), { method: 'GET', headers: auth(token) }) as Promise<PaginatedResponse<Supplier>>,
  createSupplier: (token: string, body: Record<string, unknown>) => apiRequest('/corporate/suppliers', { method: 'POST', headers: auth(token), body: JSON.stringify(body) }) as Promise<Supplier>,
  getSupplier: (token: string, id: number, org_id: number) => apiRequest(`/corporate/suppliers/${id}?org_id=${org_id}`, { method: 'GET', headers: auth(token) }) as Promise<Supplier>,
  updateSupplier: (token: string, id: number, body: Record<string, unknown>) => apiRequest(`/corporate/suppliers/${id}`, { method: 'PATCH', headers: auth(token), body: JSON.stringify(body) }) as Promise<Supplier>,

  getContracts: (token: string, query: Record<string, unknown>) => apiRequest(withQuery('/corporate/contracts', query as any), { method: 'GET', headers: auth(token) }) as Promise<PaginatedResponse<Contract>>,
  createContract: (token: string, body: Record<string, unknown>) => apiRequest('/corporate/contracts', { method: 'POST', headers: auth(token), body: JSON.stringify(body) }) as Promise<Contract>,
  getContract: (token: string, id: number, org_id: number) => apiRequest(`/corporate/contracts/${id}?org_id=${org_id}`, { method: 'GET', headers: auth(token) }) as Promise<Contract>,
  updateContract: (token: string, id: number, body: Record<string, unknown>) => apiRequest(`/corporate/contracts/${id}`, { method: 'PATCH', headers: auth(token), body: JSON.stringify(body) }) as Promise<Contract>,

  getPurchaseOrders: (token: string, query: Record<string, unknown>) => apiRequest(withQuery('/corporate/purchase-orders', query as any), { method: 'GET', headers: auth(token) }) as Promise<PaginatedResponse<PurchaseOrder>>,
  createPurchaseOrder: (token: string, body: Record<string, unknown>) => apiRequest('/corporate/purchase-orders', { method: 'POST', headers: auth(token), body: JSON.stringify(body) }) as Promise<PurchaseOrder>,
  getPurchaseOrder: (token: string, id: number, org_id: number) => apiRequest(`/corporate/purchase-orders/${id}?org_id=${org_id}`, { method: 'GET', headers: auth(token) }) as Promise<PurchaseOrder>,
  updatePurchaseOrder: (token: string, id: number, body: Record<string, unknown>) => apiRequest(`/corporate/purchase-orders/${id}`, { method: 'PATCH', headers: auth(token), body: JSON.stringify(body) }) as Promise<PurchaseOrder>,
  poAction: (token: string, id: number, action: string, body: Record<string, unknown>) => apiRequest(`/corporate/purchase-orders/${id}/${action}`, { method: 'POST', headers: auth(token), body: JSON.stringify(body) }) as Promise<PurchaseOrder>,

  getCapexRequests: (token: string, query: Record<string, unknown>) => apiRequest(withQuery('/corporate/capex-requests', query as any), { method: 'GET', headers: auth(token) }) as Promise<PaginatedResponse<CAPEXRequest>>,
  createCapexRequest: (token: string, body: Record<string, unknown>) => apiRequest('/corporate/capex-requests', { method: 'POST', headers: auth(token), body: JSON.stringify(body) }) as Promise<CAPEXRequest>,
  getCapexRequest: (token: string, id: number, org_id: number) => apiRequest(`/corporate/capex-requests/${id}?org_id=${org_id}`, { method: 'GET', headers: auth(token) }) as Promise<CAPEXRequest>,
  updateCapexRequest: (token: string, id: number, body: Record<string, unknown>) => apiRequest(`/corporate/capex-requests/${id}`, { method: 'PATCH', headers: auth(token), body: JSON.stringify(body) }) as Promise<CAPEXRequest>,
  capexAction: (token: string, id: number, action: string, body: Record<string, unknown>) => apiRequest(`/corporate/capex-requests/${id}/${action}`, { method: 'POST', headers: auth(token), body: JSON.stringify(body) }) as Promise<CAPEXRequest>,

  getApprovalQueue: (token: string, query: Record<string, unknown>) => apiRequest(withQuery('/corporate/approvals', query as any), { method: 'GET', headers: auth(token) }) as Promise<PaginatedResponse<ApprovalRecord>>,
  approvalDecision: (token: string, id: number, action: 'approve' | 'reject', body: Record<string, unknown>) => apiRequest(`/corporate/approvals/${id}/${action}`, { method: 'POST', headers: auth(token), body: JSON.stringify(body) }) as Promise<ApprovalRecord>,

  getCorporateAuditLogs: (token: string, query: Record<string, unknown>) => apiRequest(withQuery('/audit-logs', query as any), { method: 'GET', headers: auth(token) }) as Promise<PaginatedResponse<AuditLog>>,
}
