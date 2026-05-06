import { useEffect, useState } from 'react'
import { energyApi } from '../api/energy.api'
import type { EnergyAnalyticsFilter } from '../types/energy.types'

function useAsyncState<T>(loader: () => Promise<T>, deps: Array<unknown>, enabled = true) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const reload = async () => {
    if (!enabled) return
    setLoading(true)
    setError('')
    try { setData(await loader()) } catch (e: any) { setError(e?.message || 'Request failed'); setData(null) } finally { setLoading(false) }
  }
  useEffect(() => { reload() }, deps)
  return { data, loading, error, reload }
}

export const useEnergyDashboard = (token?: string, query?: EnergyAnalyticsFilter) => useAsyncState(async () => {
  const [summary, efficiency, costs, trends] = await Promise.all([
    energyApi.getDashboardSummary(token || '', query || { org_id: 0 }),
    energyApi.getEfficiency(token || '', query || { org_id: 0 }),
    energyApi.getCostsAnalytics(token || '', query || { org_id: 0 }),
    energyApi.getTrends(token || '', query || { org_id: 0 }),
  ])
  return { summary, efficiency, costs, trends }
}, [token, JSON.stringify(query)], !!token && !!query)

export const useEnergyTrends = (token?: string, query?: EnergyAnalyticsFilter) => useAsyncState(() => energyApi.getTrends(token || '', query || { org_id: 0 }), [token, JSON.stringify(query)], !!token && !!query)
export const useEnergyEfficiency = (token?: string, query?: EnergyAnalyticsFilter) => useAsyncState(() => energyApi.getEfficiency(token || '', query || { org_id: 0 }), [token, JSON.stringify(query)], !!token && !!query)
export const useEnergyCostsAnalytics = (token?: string, query?: EnergyAnalyticsFilter) => useAsyncState(() => energyApi.getCostsAnalytics(token || '', query || { org_id: 0 }), [token, JSON.stringify(query)], !!token && !!query)
export const useSustainabilityAnalytics = (token?: string, query?: EnergyAnalyticsFilter) => useAsyncState(() => energyApi.getSustainabilityAnalytics(token || '', query || { org_id: 0 }), [token, JSON.stringify(query)], !!token && !!query)

export const useEnergyKPIReadings = (token?: string, query?: Record<string, unknown>) => useAsyncState(() => energyApi.getKPIReadings(token || '', query || {}), [token, JSON.stringify(query)], !!token && !!query)
export const useEnergyKPIReadingDetail = (token?: string, id?: number, org_id?: number) => useAsyncState(() => energyApi.getKPIReading(token || '', id || 0, org_id || 0), [token, id, org_id], !!token && !!id && !!org_id)
export const useCreateEnergyKPIReading = () => energyApi.createKPIReading
export const useBulkEnergyKPIReadingUpload = () => energyApi.bulkCreateKPIReadings

export const useUtilityCosts = (token?: string, query?: Record<string, unknown>) => useAsyncState(() => energyApi.getUtilityCosts(token || '', query || {}), [token, JSON.stringify(query)], !!token && !!query)
export const useUtilityCostDetail = (token?: string, id?: number, org_id?: number) => useAsyncState(() => energyApi.getUtilityCost(token || '', id || 0, org_id || 0), [token, id, org_id], !!token && !!id && !!org_id)
export const useCreateUtilityCost = () => energyApi.createUtilityCost
export const useUpdateUtilityCost = () => energyApi.updateUtilityCost
export const useUtilityCostAction = () => energyApi.utilityCostAction

export const useSustainabilityTargets = (token?: string, query?: Record<string, unknown>) => useAsyncState(() => energyApi.getSustainabilityTargets(token || '', query || {}), [token, JSON.stringify(query)], !!token && !!query)
export const useCreateSustainabilityTarget = () => energyApi.createSustainabilityTarget
export const useUpdateSustainabilityTarget = () => energyApi.updateSustainabilityTarget

export const useEnergyAuditLogs = (token?: string, query?: Record<string, unknown>) => useAsyncState(() => energyApi.getAuditLogs(token || '', query || {}), [token, JSON.stringify(query)], !!token && !!query)
