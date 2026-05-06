import { useEffect, useState } from 'react'
import { foodBeverageApi } from '../api/foodBeverage.api'
import type {
  BreakfastCount,
  BreakfastCountFilters,
  FBAuditFilters,
  FBMetricsSummary,
  FBTask,
  FBTaskFilters,
  FBTrendPoint,
  OutletReadinessFilters,
  OutletReadinessRecord,
  PaginatedResponse,
} from '../types/foodBeverage.types'

function useAsyncState<T>(loader: () => Promise<T>, deps: Array<unknown>, enabled = true) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const reload = async () => {
    if (!enabled) return
    setLoading(true)
    setError('')
    try { setData(await loader()) } catch (err: any) { setError(err.message || 'Request failed'); setData(null) } finally { setLoading(false) }
  }
  useEffect(() => { reload() }, deps)
  return { data, loading, error, reload }
}

export function useBreakfastCounts(accessToken?: string, orgId?: number, filters?: BreakfastCountFilters) {
  return useAsyncState(() => foodBeverageApi.getBreakfastCounts(accessToken || '', orgId || 0, filters || {} as BreakfastCountFilters), [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId && !!filters)
}
export function useBreakfastCountDetail(accessToken?: string, orgId?: number, id?: number) {
  return useAsyncState(() => foodBeverageApi.getBreakfastCountDetail(accessToken || '', orgId || 0, id || 0), [accessToken, orgId, id], !!accessToken && !!orgId && !!id)
}
export const useCreateBreakfastCount = () => foodBeverageApi.createBreakfastCount
export const useUpdateBreakfastCount = () => foodBeverageApi.updateBreakfastCount

export function useOutletReadiness(accessToken?: string, orgId?: number, filters?: OutletReadinessFilters) {
  return useAsyncState(() => foodBeverageApi.getOutletReadiness(accessToken || '', orgId || 0, filters || {} as OutletReadinessFilters), [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId && !!filters)
}
export function useOutletReadinessDetail(accessToken?: string, orgId?: number, id?: number) {
  return useAsyncState(() => foodBeverageApi.getOutletReadinessDetail(accessToken || '', orgId || 0, id || 0), [accessToken, orgId, id], !!accessToken && !!orgId && !!id)
}
export const useCreateOutletReadiness = () => foodBeverageApi.createOutletReadiness
export const useUpdateOutletReadiness = () => foodBeverageApi.updateOutletReadiness
export const useOutletReadinessAction = () => foodBeverageApi.outletReadinessAction

export function useFBTasks(accessToken?: string, orgId?: number, filters?: FBTaskFilters) {
  return useAsyncState(() => foodBeverageApi.getFBTasks(accessToken || '', orgId || 0, filters || {} as FBTaskFilters), [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId && !!filters)
}
export function useFBTaskDetail(accessToken?: string, orgId?: number, id?: number) {
  return useAsyncState(() => foodBeverageApi.getFBTaskDetail(accessToken || '', orgId || 0, id || 0), [accessToken, orgId, id], !!accessToken && !!orgId && !!id)
}
export const useCreateFBTask = () => foodBeverageApi.createFBTask
export const useUpdateFBTask = () => foodBeverageApi.updateFBTask
export const useAssignFBTask = () => foodBeverageApi.assignFBTask
export const useFBTaskAction = () => foodBeverageApi.fbTaskAction

export function useFBMetrics(accessToken?: string, orgId?: number, query?: URLSearchParams) {
  const [summary, setSummary] = useState<FBMetricsSummary>({ expected_breakfast_count: 0, actual_breakfast_count: 0, variance_count: 0, variance_percentage: 0, complimentary_count: 0, paid_count: 0, no_show_count: 0, outlet_ready_count: 0, outlet_not_ready_count: 0, average_readiness_score: 0, total_tasks: 0, completed_tasks: 0, overdue_tasks: 0, average_task_completion_time: 0 })
  const [breakfastTrend, setBreakfastTrend] = useState<FBTrendPoint[]>([])
  const [readinessTrend, setReadinessTrend] = useState<FBTrendPoint[]>([])
  const [taskTrend, setTaskTrend] = useState<FBTrendPoint[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const reload = async () => {
    if (!accessToken || !orgId || !query) return
    setLoading(true); setError('')
    try {
      const q = new URLSearchParams(query.toString())
      const [s, b, r, t] = await Promise.all([
        foodBeverageApi.getFBMetricsSummary(accessToken, orgId, new URLSearchParams(q.toString())),
        foodBeverageApi.getFBMetricsBreakfast(accessToken, orgId, new URLSearchParams(q.toString())),
        foodBeverageApi.getFBMetricsReadiness(accessToken, orgId, new URLSearchParams(q.toString())),
        foodBeverageApi.getFBMetricsTasks(accessToken, orgId, new URLSearchParams(q.toString())),
      ])
      setSummary({ ...summary, ...s })
      setBreakfastTrend(b || []); setReadinessTrend(r || []); setTaskTrend(t || [])
    } catch (err: any) {
      setError(err.message || 'Failed to load metrics')
      setBreakfastTrend([]); setReadinessTrend([]); setTaskTrend([])
    } finally { setLoading(false) }
  }
  useEffect(() => { reload() }, [accessToken, orgId, query?.toString()])
  return { summary, breakfastTrend, readinessTrend, taskTrend, loading, error, reload }
}

export function useFBAuditLogs(accessToken?: string, orgId?: number, filters?: FBAuditFilters) {
  return useAsyncState(() => foodBeverageApi.getFBAuditLogs(accessToken || '', orgId || 0, filters || {} as FBAuditFilters), [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId && !!filters)
}

export type PaginatedData<T> = PaginatedResponse<T>
export type BreakfastCountData = BreakfastCount
export type OutletReadinessData = OutletReadinessRecord
export type FBTaskData = FBTask
