import { useEffect, useState } from 'react'
import {
  acknowledgeNonComplianceAlert,
  activateInspectionTemplate,
  cancelInspectionRun,
  completeInspectionRun,
  createInspectionRun,
  createInspectionTemplate,
  deactivateInspectionTemplate,
  fetchInspectionAuditLogs,
  fetchInspectionReportNonCompliance,
  fetchInspectionReportSummary,
  fetchInspectionReportTrends,
  fetchInspectionRunDetail,
  fetchInspectionRunHistory,
  fetchInspectionRuns,
  fetchInspectionTemplateDetail,
  fetchInspectionTemplates,
  fetchNonComplianceAlerts,
  resolveNonComplianceAlert,
  startInspectionRun,
  submitInspectionResponse,
  updateInspectionResponse,
  updateInspectionTemplate,
  voidInspectionRun,
} from '../api/inspections.api'
import type { InspectionAuditLogFilters, InspectionRunFilters, InspectionTemplateFilters } from '../types/inspections.types'

function useAsyncState<T>(loader: () => Promise<T>, deps: Array<unknown>, enabled = true) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const reload = async () => {
    if (!enabled) return
    setLoading(true)
    setError('')
    try {
      setData(await loader())
    } catch (err: any) {
      setData(null)
      setError(err.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { reload() }, deps)
  return { data, loading, error, reload }
}

export function useInspectionTemplates(accessToken?: string, orgId?: number, filters?: InspectionTemplateFilters) {
  return useAsyncState(() => fetchInspectionTemplates(accessToken || '', orgId || 0, filters || { q: '', category: '', department: '', property: '', is_active: '', page: 1, page_size: 10 }), [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId && !!filters)
}

export function useInspectionTemplateDetail(accessToken?: string, orgId?: number, id?: number) {
  return useAsyncState(() => fetchInspectionTemplateDetail(accessToken || '', orgId || 0, id || 0), [accessToken, orgId, id], !!accessToken && !!orgId && !!id)
}

export function useInspectionRuns(accessToken?: string, orgId?: number, filters?: InspectionRunFilters) {
  return useAsyncState(() => fetchInspectionRuns(accessToken || '', orgId || 0, filters || { template_id: '', status: '', result: '', property: '', department: '', location: '', room: '', asset: '', assigned_to: '', inspected_by: '', page: 1, page_size: 10 }), [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId && !!filters)
}

export function useInspectionRunDetail(accessToken?: string, orgId?: number, id?: number) {
  return useAsyncState(async () => {
    const [run, history] = await Promise.all([
      fetchInspectionRunDetail(accessToken || '', orgId || 0, id || 0),
      fetchInspectionRunHistory(accessToken || '', orgId || 0, id || 0),
    ])
    return { run, history: history.results }
  }, [accessToken, orgId, id], !!accessToken && !!orgId && !!id)
}

export function useInspectionReports(accessToken?: string, orgId?: number, groupBy = 'day') {
  return useAsyncState(async () => {
    const [summary, trends, nonCompliance] = await Promise.all([
      fetchInspectionReportSummary(accessToken || '', orgId || 0),
      fetchInspectionReportTrends(accessToken || '', orgId || 0, groupBy),
      fetchInspectionReportNonCompliance(accessToken || '', orgId || 0),
    ])
    return { summary, trends: trends.results, nonCompliance }
  }, [accessToken, orgId, groupBy], !!accessToken && !!orgId)
}

export function useNonComplianceAlerts(accessToken?: string, orgId?: number) {
  return useAsyncState(() => fetchNonComplianceAlerts(accessToken || '', orgId || 0), [accessToken, orgId], !!accessToken && !!orgId)
}

export function useInspectionAuditLogs(accessToken?: string, orgId?: number, filters?: InspectionAuditLogFilters) {
  return useAsyncState(() => fetchInspectionAuditLogs(accessToken || '', orgId || 0, filters || { q: '', actor_user_id: '', action: '', target_type: '', target_id: '', date_from: '', date_to: '', page: 1, page_size: 20, sort_by: 'created_at', sort_dir: 'desc' }), [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId && !!filters)
}

export const useCreateInspectionTemplate = () => createInspectionTemplate
export const useUpdateInspectionTemplate = () => updateInspectionTemplate
export const useActivateInspectionTemplate = () => activateInspectionTemplate
export const useDeactivateInspectionTemplate = () => deactivateInspectionTemplate
export const useCreateInspectionRun = () => createInspectionRun
export const useStartInspectionRun = () => startInspectionRun
export const useSubmitInspectionResponse = () => submitInspectionResponse
export const useUpdateInspectionResponse = () => updateInspectionResponse
export const useCompleteInspectionRun = () => completeInspectionRun
export const useCancelInspectionRun = () => cancelInspectionRun
export const useVoidInspectionRun = () => voidInspectionRun
export const useAcknowledgeNonComplianceAlert = () => acknowledgeNonComplianceAlert
export const useResolveNonComplianceAlert = () => resolveNonComplianceAlert
