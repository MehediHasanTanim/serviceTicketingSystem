import { apiRequest } from '../../../shared/api/client'
import type { EnergyAnalyticsFilter, EnergyAuditLog, EnergyCosts, EnergyEfficiency, EnergyKPIReading, EnergySummary, EnergyTrends, Pagination, SustainabilityAnalytics, SustainabilityTarget, UtilityCost } from '../types/energy.types'

const auth = (token: string) => ({ Authorization: `Bearer ${token}` })
const withQuery = (path: string, query: Record<string, unknown>) => {
  const params = new URLSearchParams()
  Object.entries(query).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') params.set(k, String(v))
  })
  const q = params.toString()
  return q ? `${path}?${q}` : path
}

export const energyApi = {
  getDashboardSummary: (token: string, query: EnergyAnalyticsFilter) => apiRequest(withQuery('/energy/analytics/summary', query as any), { method: 'GET', headers: auth(token) }) as Promise<EnergySummary>,
  getTrends: (token: string, query: EnergyAnalyticsFilter) => apiRequest(withQuery('/energy/analytics/trends', query as any), { method: 'GET', headers: auth(token) }) as Promise<EnergyTrends>,
  getEfficiency: (token: string, query: EnergyAnalyticsFilter) => apiRequest(withQuery('/energy/analytics/efficiency', query as any), { method: 'GET', headers: auth(token) }) as Promise<EnergyEfficiency>,
  getCostsAnalytics: (token: string, query: EnergyAnalyticsFilter) => apiRequest(withQuery('/energy/analytics/costs', query as any), { method: 'GET', headers: auth(token) }) as Promise<EnergyCosts>,
  getSustainabilityAnalytics: (token: string, query: EnergyAnalyticsFilter) => apiRequest(withQuery('/energy/analytics/sustainability', query as any), { method: 'GET', headers: auth(token) }) as Promise<SustainabilityAnalytics>,

  getKPIReadings: (token: string, query: Record<string, unknown>) => apiRequest(withQuery('/energy/kpi-readings', query), { method: 'GET', headers: auth(token) }) as Promise<Pagination<EnergyKPIReading>>,
  getKPIReading: (token: string, id: number, org_id: number) => apiRequest(`/energy/kpi-readings/${id}?org_id=${org_id}`, { method: 'GET', headers: auth(token) }) as Promise<EnergyKPIReading>,
  createKPIReading: (token: string, body: Record<string, unknown>) => apiRequest('/energy/kpi-readings', { method: 'POST', headers: auth(token), body: JSON.stringify(body) }) as Promise<EnergyKPIReading>,
  bulkCreateKPIReadings: (token: string, body: Record<string, unknown>) => apiRequest('/energy/kpi-readings/bulk', { method: 'POST', headers: auth(token), body: JSON.stringify(body) }) as Promise<{ count: number; created: number; results: EnergyKPIReading[] }>,

  getUtilityCosts: (token: string, query: Record<string, unknown>) => apiRequest(withQuery('/energy/utility-costs', query), { method: 'GET', headers: auth(token) }) as Promise<Pagination<UtilityCost>>,
  getUtilityCost: (token: string, id: number, org_id: number) => apiRequest(`/energy/utility-costs/${id}?org_id=${org_id}`, { method: 'GET', headers: auth(token) }) as Promise<UtilityCost>,
  createUtilityCost: (token: string, body: Record<string, unknown>) => apiRequest('/energy/utility-costs', { method: 'POST', headers: auth(token), body: JSON.stringify(body) }) as Promise<UtilityCost>,
  updateUtilityCost: (token: string, id: number, body: Record<string, unknown>) => apiRequest(`/energy/utility-costs/${id}`, { method: 'PATCH', headers: auth(token), body: JSON.stringify(body) }) as Promise<UtilityCost>,
  utilityCostAction: (token: string, id: number, action: 'submit' | 'approve' | 'mark-paid' | 'void', body: Record<string, unknown>) => apiRequest(`/energy/utility-costs/${id}/${action}`, { method: 'POST', headers: auth(token), body: JSON.stringify(body) }) as Promise<UtilityCost>,

  getSustainabilityTargets: (token: string, query: Record<string, unknown>) => apiRequest(withQuery('/energy/sustainability-targets', query), { method: 'GET', headers: auth(token) }) as Promise<Pagination<SustainabilityTarget>>,
  createSustainabilityTarget: (token: string, body: Record<string, unknown>) => apiRequest('/energy/sustainability-targets', { method: 'POST', headers: auth(token), body: JSON.stringify(body) }) as Promise<SustainabilityTarget>,
  updateSustainabilityTarget: (token: string, id: number, body: Record<string, unknown>) => apiRequest(`/energy/sustainability-targets/${id}`, { method: 'PATCH', headers: auth(token), body: JSON.stringify(body) }) as Promise<SustainabilityTarget>,

  getAuditLogs: (token: string, query: Record<string, unknown>) => apiRequest(withQuery('/audit-logs', query), { method: 'GET', headers: auth(token) }) as Promise<Pagination<EnergyAuditLog>>,
}
