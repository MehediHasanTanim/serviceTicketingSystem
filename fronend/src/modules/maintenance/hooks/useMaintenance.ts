import { useEffect, useState } from 'react'
import {
  assignMaintenanceOrder,
  createAsset,
  createMaintenanceLogbookEntry,
  createMaintenanceOrder,
  createPMSchedule,
  createTaskFromQR,
  fetchAsset,
  fetchAssetHistory,
  fetchAssets,
  fetchMaintenanceAuditLogs,
  fetchMaintenanceLogbook,
  fetchMaintenanceOrder,
  fetchMaintenanceOrders,
  fetchPMSchedules,
  lookupAssetByQR,
  mapTasksToCalendarItems,
  recalculateMaintenanceCosts,
  runPMScheduler,
  transitionAssetStatus,
  transitionMaintenanceOrder,
  updateAsset,
  updateMaintenanceOrder,
  updatePMSchedule,
} from '../api/maintenance.api'
import type { AssetFilters, AuditLogFilters, MaintenanceOrderFilters } from '../types/maintenance.types'

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
      setError(err.message || 'Request failed')
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { reload() }, deps)
  return { data, loading, error, reload }
}

export function useMaintenanceOrders(accessToken?: string, orgId?: number, filters?: MaintenanceOrderFilters) {
  return useAsyncState(() => fetchMaintenanceOrders(accessToken || '', orgId || 0, filters || { q: '', task_type: '', status: '', priority: '', asset: '', room: '', property: '', department: '', assigned_to: '', date_from: '', date_to: '', page: 1, page_size: 10 }), [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId && !!filters)
}
export function useMaintenanceOrderDetail(accessToken?: string, orgId?: number, taskId?: number) {
  return useAsyncState(() => fetchMaintenanceOrder(accessToken || '', orgId || 0, taskId || 0), [accessToken, orgId, taskId], !!accessToken && !!orgId && !!taskId)
}
export const useCreateMaintenanceOrder = () => createMaintenanceOrder
export const useUpdateMaintenanceOrder = () => updateMaintenanceOrder
export const useMaintenanceTaskAction = () => ({ assignMaintenanceOrder, transitionMaintenanceOrder })
export function useMaintenanceLogbook(accessToken?: string, orgId?: number, taskId?: number) {
  return useAsyncState(() => fetchMaintenanceLogbook(accessToken || '', orgId || 0, taskId || 0), [accessToken, orgId, taskId], !!accessToken && !!orgId && !!taskId)
}
export const useCreateLogbookEntry = () => createMaintenanceLogbookEntry

export function usePMSchedules(accessToken?: string, orgId?: number, page = 1, page_size = 50) {
  return useAsyncState(() => fetchPMSchedules(accessToken || '', orgId || 0, { page, page_size }), [accessToken, orgId, page, page_size], !!accessToken && !!orgId)
}
export const useCreatePMSchedule = () => createPMSchedule
export const useUpdatePMSchedule = () => updatePMSchedule
export const useRunPMScheduler = () => runPMScheduler

export function usePMCalendar(accessToken?: string, orgId?: number, filters?: MaintenanceOrderFilters) {
  const query = useMaintenanceOrders(accessToken, orgId, filters)
  return { ...query, calendarItems: mapTasksToCalendarItems(query.data?.results || []) }
}

export function useAssets(accessToken?: string, orgId?: number, filters?: AssetFilters) {
  return useAsyncState(() => fetchAssets(accessToken || '', orgId || 0, filters || { q: '', status: '', category: '', location: '', room: '', department: '', property: '', criticality: '', warranty_expiring_before: '', page: 1, page_size: 10 }), [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId && !!filters)
}
export function useAssetDetail(accessToken?: string, orgId?: number, assetId?: number) {
  return useAsyncState(async () => {
    const [asset, history] = await Promise.all([
      fetchAsset(accessToken || '', orgId || 0, assetId || 0),
      fetchAssetHistory(accessToken || '', orgId || 0, assetId || 0),
    ])
    return { asset, history: history.results }
  }, [accessToken, orgId, assetId], !!accessToken && !!orgId && !!assetId)
}
export const useCreateAsset = () => createAsset
export const useUpdateAsset = () => updateAsset
export const useAssetStatusTransition = () => transitionAssetStatus

export function useQRAssetLookup(accessToken?: string, orgId?: number, qrCode?: string) {
  return useAsyncState(() => lookupAssetByQR(accessToken || '', orgId || 0, qrCode || ''), [accessToken, orgId, qrCode], !!accessToken && !!orgId && !!qrCode)
}
export const useCreateTaskFromQR = () => createTaskFromQR

export function useMaintenanceAuditLogs(accessToken?: string, orgId?: number, filters?: AuditLogFilters) {
  return useAsyncState(() => fetchMaintenanceAuditLogs(accessToken || '', orgId || 0, filters || { q: '', property_id: '', actor_user_id: '', action: '', target_type: '', target_id: '', date_from: '', date_to: '', page: 1, page_size: 20, sort_by: 'created_at', sort_dir: 'desc' }), [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId && !!filters)
}

export const useRecalculateMaintenanceCosts = () => recalculateMaintenanceCosts
