import { useEffect, useState } from 'react'
import { fetchHousekeepingKpiStaff, fetchHousekeepingKpiSummary, fetchHousekeepingKpiTurnaround } from '../api/housekeeping.api'
import type { HousekeepingKpiSummary, HousekeepingStaffPerformance, HousekeepingTurnaround } from '../types/housekeeping.types'

export type HousekeepingKpiFilters = {
  org_id: number
  property_id?: string
  floor_id?: string
  date_from?: string
  date_to?: string
  staff_id?: string
  room_type?: string
}

const zeroSummary: HousekeepingKpiSummary = {
  total_tasks_created: 0,
  total_tasks_completed: 0,
  pending_tasks_count: 0,
  overdue_tasks_count: 0,
  avg_completion_minutes: 0,
  avg_room_turnaround_minutes: 0,
  sla_compliance_pct: 0,
}

export function useHousekeepingKpis(accessToken?: string, filters?: HousekeepingKpiFilters) {
  const [summary, setSummary] = useState<HousekeepingKpiSummary>(zeroSummary)
  const [staff, setStaff] = useState<HousekeepingStaffPerformance[]>([])
  const [turnaround, setTurnaround] = useState<HousekeepingTurnaround>({ events: 0, average_minutes: 0 })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    if (!accessToken || !filters?.org_id) return
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams()
      params.set('org_id', String(filters.org_id))
      if (filters.property_id) params.set('property_id', filters.property_id)
      if (filters.floor_id) params.set('floor_id', filters.floor_id)
      if (filters.date_from) params.set('date_from', filters.date_from)
      if (filters.date_to) params.set('date_to', filters.date_to)
      if (filters.staff_id) params.set('staff_id', filters.staff_id)
      if (filters.room_type) params.set('room_type', filters.room_type)

      const [s, st, t] = await Promise.all([
        fetchHousekeepingKpiSummary(accessToken, params),
        fetchHousekeepingKpiStaff(accessToken, params),
        fetchHousekeepingKpiTurnaround(accessToken, params),
      ])
      setSummary({ ...zeroSummary, ...s })
      setStaff(st)
      setTurnaround({ ...t })
    } catch (err: any) {
      setError(err.message || 'Failed to load KPI data.')
      setSummary(zeroSummary)
      setStaff([])
      setTurnaround({ events: 0, average_minutes: 0 })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [accessToken, filters?.org_id, filters?.property_id, filters?.floor_id, filters?.date_from, filters?.date_to, filters?.staff_id, filters?.room_type])

  return { summary, staff, turnaround, loading, error, reload: load }
}
