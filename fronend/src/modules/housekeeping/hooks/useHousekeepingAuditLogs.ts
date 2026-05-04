import { useEffect, useState } from 'react'
import { fetchHousekeepingAuditLogs } from '../api/housekeeping.api'
import type { HousekeepingAuditLog } from '../types/housekeeping.types'

export type HousekeepingAuditFilters = {
  org_id: number
  q: string
  actor_user_id: string
  action: string
  target_type: string
  target_id: string
  date_from: string
  date_to: string
  page: number
  page_size: number
  sort_by: 'created_at' | 'action' | 'target_type'
  sort_dir: 'asc' | 'desc'
}

export function useHousekeepingAuditLogs(accessToken?: string, filters?: HousekeepingAuditFilters) {
  const [rows, setRows] = useState<HousekeepingAuditLog[]>([])
  const [count, setCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    if (!accessToken || !filters?.org_id) return
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams()
      params.set('org_id', String(filters.org_id))
      params.set('page', String(filters.page))
      params.set('page_size', String(filters.page_size))
      params.set('sort_by', filters.sort_by)
      params.set('sort_dir', filters.sort_dir)
      if (filters.q.trim()) params.set('q', filters.q.trim())
      if (filters.actor_user_id.trim()) params.set('actor_user_id', filters.actor_user_id.trim())
      if (filters.action.trim()) params.set('action', filters.action.trim())
      if (filters.target_type.trim()) params.set('target_type', filters.target_type.trim())
      if (filters.target_id.trim()) params.set('target_id', filters.target_id.trim())
      if (filters.date_from) params.set('date_from', filters.date_from)
      if (filters.date_to) params.set('date_to', filters.date_to)

      const data = await fetchHousekeepingAuditLogs(accessToken, params)
      setRows(data.results || [])
      setCount(data.count || 0)
    } catch (err: any) {
      setError(err.message || 'Failed to load audit logs.')
      setRows([])
      setCount(0)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [accessToken, filters?.org_id, filters?.page, filters?.page_size, filters?.sort_by, filters?.sort_dir, filters?.q, filters?.actor_user_id, filters?.action, filters?.target_type, filters?.target_id, filters?.date_from, filters?.date_to])

  return { rows, count, loading, error, reload: load }
}
