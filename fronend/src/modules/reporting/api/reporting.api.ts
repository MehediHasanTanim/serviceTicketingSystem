import { apiRequest } from '../../../shared/api/client'
import type { AuditLogRow, ComplianceAnalytics, CostsAnalytics, DepartmentPerformance, EnergyAnalytics, ExecutiveSummary, PaginatedResponse, ReportDefinitionCreatePayload, ReportDefinitionDetail, ReportDefinitionListItem, ReportDefinitionUpdatePayload, ReportDownloadResponse, ReportRunDetail, ReportRunListItem, ReportRunRequestPayload, ReportRunResponse, ReportScheduleCreatePayload, ReportScheduleDetail, ReportScheduleListItem, ReportScheduleResponse, ReportScheduleUpdatePayload, ReportingMetricFilters, ScheduleRunDueSummary, SlaAnalytics } from '../types/reporting.types'
const auth = (token: string) => ({ Authorization: `Bearer ${token}` })
const withQuery = (path: string, query: Record<string, unknown>) => { const p = new URLSearchParams(); Object.entries(query).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== '') p.set(k, String(v)) }); const q = p.toString(); return q ? `${path}?${q}` : path }
export const reportingApi = {
  getExecutiveSummary: (token: string, query: ReportingMetricFilters) => apiRequest(withQuery('/reporting/analytics/executive-summary', query as Record<string, unknown>), { method: 'GET', headers: auth(token) }) as Promise<ExecutiveSummary>,
  getDepartmentPerformance: (token: string, query: ReportingMetricFilters) => apiRequest(withQuery('/reporting/analytics/department-performance', query as Record<string, unknown>), { method: 'GET', headers: auth(token) }) as Promise<DepartmentPerformance>,
  getSla: (token: string, query: ReportingMetricFilters) => apiRequest(withQuery('/reporting/analytics/sla', query as Record<string, unknown>), { method: 'GET', headers: auth(token) }) as Promise<SlaAnalytics>,
  getCosts: (token: string, query: ReportingMetricFilters) => apiRequest(withQuery('/reporting/analytics/costs', query as Record<string, unknown>), { method: 'GET', headers: auth(token) }) as Promise<CostsAnalytics>,
  getCompliance: (token: string, query: ReportingMetricFilters) => apiRequest(withQuery('/reporting/analytics/compliance', query as Record<string, unknown>), { method: 'GET', headers: auth(token) }) as Promise<ComplianceAnalytics>,
  getEnergy: (token: string, query: ReportingMetricFilters) => apiRequest(withQuery('/reporting/analytics/energy', query as Record<string, unknown>), { method: 'GET', headers: auth(token) }) as Promise<EnergyAnalytics>,
  createReportDefinition: (token: string, body: ReportDefinitionCreatePayload) => apiRequest('/reporting/definitions', { method: 'POST', headers: auth(token), body: JSON.stringify(body) }),
  getReportDefinitions: (token: string) => apiRequest('/reporting/definitions', { method: 'GET', headers: auth(token) }) as Promise<PaginatedResponse<ReportDefinitionListItem>>,
  getReportDefinitionDetail: (token: string, id: number) => apiRequest(`/reporting/definitions/${id}`, { method: 'GET', headers: auth(token) }) as Promise<ReportDefinitionDetail>,
  updateReportDefinition: (token: string, id: number, body: ReportDefinitionUpdatePayload) => apiRequest(`/reporting/definitions/${id}`, { method: 'PATCH', headers: auth(token), body: JSON.stringify(body) }),
  runReport: (token: string, body: ReportRunRequestPayload) => apiRequest('/reporting/reports/run', { method: 'POST', headers: auth(token), body: JSON.stringify(body) }) as Promise<ReportRunResponse>,
  getReportRuns: (token: string) => apiRequest('/reporting/reports/runs', { method: 'GET', headers: auth(token) }) as Promise<PaginatedResponse<ReportRunListItem>>,
  getReportRunDetail: (token: string, id: number) => apiRequest(`/reporting/reports/runs/${id}`, { method: 'GET', headers: auth(token) }) as Promise<ReportRunDetail>,
  downloadReport: (token: string, id: number) => apiRequest(`/reporting/reports/runs/${id}/download`, { method: 'GET', headers: auth(token) }) as Promise<ReportDownloadResponse>,
  createReportSchedule: (token: string, body: ReportScheduleCreatePayload) => apiRequest('/reporting/schedules', { method: 'POST', headers: auth(token), body: JSON.stringify(body) }) as Promise<ReportScheduleResponse>,
  getReportSchedules: (token: string) => apiRequest('/reporting/schedules', { method: 'GET', headers: auth(token) }) as Promise<PaginatedResponse<ReportScheduleListItem>>,
  getReportScheduleDetail: (token: string, id: number) => apiRequest(`/reporting/schedules/${id}`, { method: 'GET', headers: auth(token) }) as Promise<ReportScheduleDetail>,
  updateReportSchedule: (token: string, id: number, body: ReportScheduleUpdatePayload) => apiRequest(`/reporting/schedules/${id}`, { method: 'PATCH', headers: auth(token), body: JSON.stringify(body) }),
  activateReportSchedule: (token: string, id: number) => apiRequest(`/reporting/schedules/${id}/activate`, { method: 'POST', headers: auth(token) }),
  deactivateReportSchedule: (token: string, id: number) => apiRequest(`/reporting/schedules/${id}/deactivate`, { method: 'POST', headers: auth(token) }),
  runDueReportSchedules: (token: string) => apiRequest('/reporting/schedules/run-due', { method: 'POST', headers: auth(token) }) as Promise<ScheduleRunDueSummary>,
  getReportingAuditLogs: (token: string, query: Record<string, unknown>) => apiRequest(withQuery('/audit-logs', query), { method: 'GET', headers: auth(token) }) as Promise<PaginatedResponse<AuditLogRow>>,
}
