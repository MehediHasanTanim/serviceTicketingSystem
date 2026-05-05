import { apiRequest } from '../../../shared/api/client'
import type {
  ApprovalTrailEntry,
  AuditRecord,
  AuditRecordDetail,
  ComplianceCheck,
  ComplianceCheckFilters,
  ComplianceRequirement,
  ComplianceRequirementFilters,
  ComplianceStatusBreakdown,
  DashboardSummary,
  LegalExpiryTimeline,
  LegalRecord,
  LegalRecordDetail,
  LegalRecordFilters,
  PaginatedResponse,
  RiskComplianceAlert,
  RiskComplianceAuditLog,
  RiskComplianceAuditLogFilters,
  RiskFilters,
  RiskMitigation,
  RiskRegistryItem,
  RiskSummaryBreakdown,
} from '../types/riskCompliance.types'

function authHeader(token: string) {
  return { Authorization: `Bearer ${token}` }
}

function setParam(params: URLSearchParams, key: string, value: string | number | undefined) {
  if (value === undefined || value === '' || value === null) return
  params.set(key, String(value))
}

export async function fetchComplianceRequirements(accessToken: string, orgId: number, filters: ComplianceRequirementFilters) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  setParam(params, 'q', filters.q)
  setParam(params, 'category', filters.category)
  setParam(params, 'property', filters.property)
  setParam(params, 'department', filters.department)
  setParam(params, 'owner', filters.owner)
  setParam(params, 'priority', filters.priority)
  setParam(params, 'status', filters.status)
  setParam(params, 'page', filters.page)
  setParam(params, 'page_size', filters.page_size)
  return apiRequest(`/risk-compliance/requirements?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<ComplianceRequirement>>
}

export async function fetchComplianceRequirementDetail(accessToken: string, orgId: number, id: number) {
  return apiRequest(`/risk-compliance/requirements/${id}?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<ComplianceRequirement>
}

export async function createComplianceRequirement(accessToken: string, payload: Record<string, unknown>) {
  return apiRequest('/risk-compliance/requirements', { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<ComplianceRequirement>
}

export async function updateComplianceRequirement(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/risk-compliance/requirements/${id}`, { method: 'PATCH', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<ComplianceRequirement>
}

export async function activateComplianceRequirement(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/risk-compliance/requirements/${id}/activate`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<ComplianceRequirement>
}

export async function deactivateComplianceRequirement(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/risk-compliance/requirements/${id}/deactivate`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<ComplianceRequirement>
}

export async function fetchComplianceChecks(accessToken: string, orgId: number, filters: ComplianceCheckFilters) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  setParam(params, 'requirement_id', filters.requirement_id)
  setParam(params, 'status', filters.status)
  setParam(params, 'property', filters.property)
  setParam(params, 'department', filters.department)
  setParam(params, 'owner', filters.owner)
  setParam(params, 'assigned_to', filters.assigned_to)
  setParam(params, 'priority', filters.priority)
  setParam(params, 'category', filters.category)
  setParam(params, 'page', filters.page)
  setParam(params, 'page_size', filters.page_size)
  return apiRequest(`/risk-compliance/checks?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<ComplianceCheck>>
}

export async function fetchComplianceCheckDetail(accessToken: string, orgId: number, id: number) {
  return apiRequest(`/risk-compliance/checks/${id}?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<ComplianceCheck>
}

export async function submitComplianceCheck(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/risk-compliance/checks/${id}/submit`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<ComplianceCheck>
}

export async function waiveComplianceCheck(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/risk-compliance/checks/${id}/waive`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<ComplianceCheck>
}

export async function fetchRiskRegistry(accessToken: string, orgId: number, filters: RiskFilters) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  setParam(params, 'q', filters.q)
  setParam(params, 'category', filters.category)
  setParam(params, 'property', filters.property)
  setParam(params, 'department', filters.department)
  setParam(params, 'owner', filters.owner)
  setParam(params, 'risk_level', filters.risk_level)
  setParam(params, 'status', filters.status)
  setParam(params, 'due_from', filters.due_from)
  setParam(params, 'due_to', filters.due_to)
  setParam(params, 'page', filters.page)
  setParam(params, 'page_size', filters.page_size)
  return apiRequest(`/risk-compliance/risks?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<RiskRegistryItem>>
}

export async function fetchRiskDetail(accessToken: string, orgId: number, id: number) {
  return apiRequest(`/risk-compliance/risks/${id}?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<RiskRegistryItem>
}

export async function createRisk(accessToken: string, payload: Record<string, unknown>) {
  return apiRequest('/risk-compliance/risks', { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<RiskRegistryItem>
}

export async function updateRisk(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/risk-compliance/risks/${id}`, { method: 'PATCH', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<RiskRegistryItem>
}

export async function fetchRiskMitigations(accessToken: string, orgId: number, riskId: number) {
  return apiRequest(`/risk-compliance/risks/${riskId}/mitigations?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<RiskMitigation>>
}

export async function createMitigation(accessToken: string, riskId: number, payload: Record<string, unknown>) {
  return apiRequest(`/risk-compliance/risks/${riskId}/mitigations`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<{ id: number; risk_id: number; status: string }>
}

export async function completeMitigation(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/risk-compliance/mitigations/${id}/complete`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<{ mitigation_id: number; status: string; risk_residual_score: number; risk_status: string }>
}

export async function fetchLegalRecords(accessToken: string, orgId: number, filters: LegalRecordFilters) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  setParam(params, 'q', filters.q)
  setParam(params, 'type', filters.type)
  setParam(params, 'status', filters.status)
  setParam(params, 'property', filters.property)
  setParam(params, 'department', filters.department)
  setParam(params, 'owner', filters.owner)
  setParam(params, 'expiry_from', filters.expiry_from)
  setParam(params, 'expiry_to', filters.expiry_to)
  setParam(params, 'page', filters.page)
  setParam(params, 'page_size', filters.page_size)
  return apiRequest(`/risk-compliance/legal-records?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<LegalRecord>>
}

export async function fetchLegalRecordDetail(accessToken: string, orgId: number, id: number) {
  return apiRequest(`/risk-compliance/legal-records/${id}?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<LegalRecordDetail>
}

export async function createLegalRecord(accessToken: string, payload: Record<string, unknown>) {
  return apiRequest('/risk-compliance/legal-records', { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<LegalRecordDetail>
}

export async function updateLegalRecord(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/risk-compliance/legal-records/${id}`, { method: 'PATCH', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<LegalRecordDetail>
}

export async function fetchAuditRecords(accessToken: string, orgId: number) {
  return apiRequest(`/risk-compliance/audit-records?org_id=${orgId}&page=1&page_size=50`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<AuditRecord>>
}

export async function fetchAuditRecordDetail(accessToken: string, orgId: number, id: number) {
  return apiRequest(`/risk-compliance/audit-records/${id}?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<AuditRecordDetail>
}

export async function createAuditRecord(accessToken: string, payload: Record<string, unknown>) {
  return apiRequest('/risk-compliance/audit-records', { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<AuditRecordDetail>
}

export async function fetchRiskComplianceDashboardSummary(accessToken: string, orgId: number) {
  return apiRequest(`/risk-compliance/dashboard/summary?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<DashboardSummary>
}

export async function fetchRiskComplianceDashboardStatus(accessToken: string, orgId: number) {
  return apiRequest(`/risk-compliance/dashboard/compliance-status?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<ComplianceStatusBreakdown>
}

export async function fetchRiskComplianceDashboardRiskSummary(accessToken: string, orgId: number) {
  return apiRequest(`/risk-compliance/dashboard/risk-summary?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<RiskSummaryBreakdown>
}

export async function fetchRiskComplianceDashboardLegalExpiry(accessToken: string, orgId: number, withinDays = 30) {
  return apiRequest(`/risk-compliance/dashboard/legal-expiry?org_id=${orgId}&within_days=${withinDays}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<LegalExpiryTimeline>
}

export async function fetchRiskComplianceAlerts(accessToken: string, orgId: number) {
  return apiRequest(`/risk-compliance/alerts?org_id=${orgId}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<RiskComplianceAlert>>
}

export async function acknowledgeRiskComplianceAlert(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/risk-compliance/alerts/${id}/acknowledge`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<{ id: number; status: string }>
}

export async function resolveRiskComplianceAlert(accessToken: string, id: number, payload: Record<string, unknown>) {
  return apiRequest(`/risk-compliance/alerts/${id}/resolve`, { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<{ id: number; status: string }>
}

export async function fetchRiskComplianceAuditLogs(accessToken: string, orgId: number, filters: RiskComplianceAuditLogFilters) {
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
  return apiRequest(`/risk-compliance/audit-logs?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<RiskComplianceAuditLog>>
}

export async function fetchApprovalTrail(accessToken: string, orgId: number, entityType: string, entityId: string | number) {
  const params = new URLSearchParams()
  setParam(params, 'org_id', orgId)
  setParam(params, 'entity_type', entityType)
  setParam(params, 'entity_id', entityId)
  return apiRequest(`/risk-compliance/approval-trails?${params.toString()}`, { method: 'GET', headers: authHeader(accessToken) }) as Promise<PaginatedResponse<ApprovalTrailEntry>>
}

export async function decideApprovalTrail(accessToken: string, payload: Record<string, unknown>) {
  return apiRequest('/risk-compliance/approval-trails', { method: 'POST', headers: authHeader(accessToken), body: JSON.stringify(payload) }) as Promise<{ entity_type: string; entity_id: string; decision: string; comment: string }>
}
