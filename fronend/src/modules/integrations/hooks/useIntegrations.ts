import { useEffect, useState } from 'react'
import {
  acknowledgeIntegrationAlert,
  activateIntegrationProvider,
  createIntegrationProvider,
  deactivateIntegrationProvider,
  fetchIntegrationAlerts,
  fetchDeadLetterJobs,
  fetchIntegrationAuditLogs,
  fetchIntegrationFailureMetrics,
  fetchIntegrationJobDetail,
  fetchIntegrationJobs,
  fetchIntegrationMetricsSummary,
  fetchIntegrationProviderDetail,
  fetchIntegrationProviders,
  fetchIntegrationsHealth,
  fetchProviderHealth,
  moveIntegrationJobToDeadLetter,
  retryIntegrationJob,
  resolveIntegrationAlert,
  runProviderHealthCheck,
  updateIntegrationProvider,
} from '../api/integrations.api'
import type { IntegrationAuditLogFilters, IntegrationJobsFilters, IntegrationProvidersFilters } from '../types/integrations.types'

function useAsyncState<T>(loader: () => Promise<T>, deps: Array<unknown>, enabled = true) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const reload = async () => {
    if (!enabled) return
    setLoading(true)
    setError('')
    try { setData(await loader()) } catch (err: any) { setData(null); setError(err?.message || 'Request failed') } finally { setLoading(false) }
  }
  useEffect(() => { reload() }, deps)
  return { data, loading, error, reload }
}

export const useIntegrationProviders = (token?: string, orgId?: number, filters?: IntegrationProvidersFilters) => useAsyncState(() => fetchIntegrationProviders(token || '', orgId || 0, filters || { q: '', provider_type: '', status: '', auth_type: '', date_from: '', date_to: '', page: 1, page_size: 10, sort_by: 'updated_at', sort_dir: 'desc' }), [token, orgId, JSON.stringify(filters)], !!token && !!orgId && !!filters)
export const useIntegrationProviderDetail = (token?: string, id?: number) => useAsyncState(() => fetchIntegrationProviderDetail(token || '', id || 0), [token, id], !!token && !!id)
export const useIntegrationsHealth = (token?: string, orgId?: number) => useAsyncState(() => fetchIntegrationsHealth(token || '', orgId || 0), [token, orgId], !!token && !!orgId)
export const useIntegrationMetricsSummary = (token?: string, orgId?: number) => useAsyncState(() => fetchIntegrationMetricsSummary(token || '', orgId || 0), [token, orgId], !!token && !!orgId)
export const useIntegrationFailureMetrics = (token?: string, orgId?: number) => useAsyncState(() => fetchIntegrationFailureMetrics(token || '', orgId || 0), [token, orgId], !!token && !!orgId)
export const useProviderHealth = (token?: string, id?: number) => useAsyncState(() => fetchProviderHealth(token || '', id || 0), [token, id], !!token && !!id)

export const useIntegrationJobs = (token?: string, orgId?: number, filters?: IntegrationJobsFilters) => useAsyncState(() => fetchIntegrationJobs(token || '', orgId || 0, filters || { provider: '', job_type: '', direction: '', status: '', source_entity_type: '', target_entity_type: '', date_from: '', date_to: '', correlation_id: '', page: 1, page_size: 10 }), [token, orgId, JSON.stringify(filters)], !!token && !!orgId && !!filters)
export const useIntegrationJobDetail = (token?: string, orgId?: number, id?: number) => useAsyncState(() => fetchIntegrationJobDetail(token || '', id || 0, orgId || 0), [token, orgId, id], !!token && !!orgId && !!id)
export const useDeadLetterJobs = (token?: string, orgId?: number, page = 1, pageSize = 20) => useAsyncState(() => fetchDeadLetterJobs(token || '', orgId || 0, page, pageSize), [token, orgId, page, pageSize], !!token && !!orgId)

export const useIntegrationAuditLogs = (token?: string, orgId?: number, filters?: IntegrationAuditLogFilters) => useAsyncState(() => fetchIntegrationAuditLogs(token || '', orgId || 0, filters || { q: '', actor_user_id: '', action: 'integration_', target_type: '', target_id: '', provider: '', job: '', date_from: '', date_to: '', page: 1, page_size: 20, sort_by: 'created_at', sort_dir: 'desc' }), [token, orgId, JSON.stringify(filters)], !!token && !!orgId && !!filters)

export const useCreateIntegrationProvider = () => createIntegrationProvider
export const useUpdateIntegrationProvider = () => updateIntegrationProvider
export const useActivateIntegrationProvider = () => activateIntegrationProvider
export const useDeactivateIntegrationProvider = () => deactivateIntegrationProvider
export const useProviderHealthCheck = () => runProviderHealthCheck
export const useRetryIntegrationJob = () => retryIntegrationJob
export const useMoveIntegrationJobToDeadLetter = () => moveIntegrationJobToDeadLetter
export const useIntegrationAlerts = (token?: string, orgId?: number, query?: Record<string, unknown>) => useAsyncState(() => fetchIntegrationAlerts(token || '', orgId || 0, query || {}), [token, orgId, JSON.stringify(query)], !!token && !!orgId)
export const useAcknowledgeIntegrationAlert = () => acknowledgeIntegrationAlert
export const useResolveIntegrationAlert = () => resolveIntegrationAlert
