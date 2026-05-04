import { useEffect, useState } from 'react'
import { fetchHousekeepingTasks } from '../api/housekeeping.api'
import type { HousekeepingTaskFilters, HousekeepingTaskLike } from '../types/housekeeping.types'

export function useHousekeepingTasks(accessToken?: string, orgId?: number, filters?: HousekeepingTaskFilters) {
  const [data, setData] = useState<HousekeepingTaskLike[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    if (!accessToken || !orgId || !filters) return
    setLoading(true)
    setError('')
    try {
      setData(await fetchHousekeepingTasks(accessToken, orgId, filters))
    } catch (err: any) {
      setError(err.message || 'Failed to load housekeeping tasks.')
      setData([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [accessToken, orgId, filters?.date, filters?.property, filters?.floor, filters?.room, filters?.staff, filters?.priority, filters?.taskType, filters?.status, filters?.q])

  return { data, loading, error, reload: load }
}
