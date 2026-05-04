import { useEffect, useState } from 'react'
import { fetchHousekeepingTaskDetail } from '../api/housekeeping.api'
import type { HousekeepingTaskLike } from '../types/housekeeping.types'

export function useHousekeepingTaskDetail(accessToken?: string, orgId?: number, taskId?: number) {
  const [data, setData] = useState<HousekeepingTaskLike | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    if (!accessToken || !orgId || !taskId) return
    setLoading(true)
    setError('')
    try {
      const row = await fetchHousekeepingTaskDetail(accessToken, taskId, orgId)
      const status = row.status === 'COMPLETED' && (row.notes || '').includes('[verified]') ? 'VERIFIED' : row.status
      const dueAt = row.due_at
      setData({
        id: String(row.id),
        roomNumber: String(row.room_id),
        taskType: row.task_type,
        priority: row.priority,
        status,
        assignedStaff: row.assigned_to ? `#${row.assigned_to}` : undefined,
        dueAt,
        overdue: !!dueAt && new Date(dueAt).getTime() < Date.now() && !['COMPLETED', 'VERIFIED', 'CANCELLED'].includes(status),
        source: 'audit',
      })
    } catch (err: any) {
      setError(err.message || 'Failed to load task detail.')
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [accessToken, orgId, taskId])

  return { data, loading, error, reload: load }
}
