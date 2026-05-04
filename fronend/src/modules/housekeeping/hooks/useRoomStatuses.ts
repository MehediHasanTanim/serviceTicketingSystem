import { useEffect, useState } from 'react'
import { fetchRoomStatuses, updateRoomStatus } from '../api/housekeeping.api'
import type { RoomStatusRow } from '../types/housekeeping.types'

export function useRoomStatuses(accessToken?: string, propertyId?: number) {
  const [data, setData] = useState<RoomStatusRow[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    if (!accessToken) return
    setLoading(true)
    setError('')
    try {
      setData(await fetchRoomStatuses(accessToken, propertyId))
    } catch (err: any) {
      setError(err.message || 'Failed to load room statuses.')
      setData([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [accessToken, propertyId])

  return { data, loading, error, reload: load }
}

export function useUpdateRoomStatus(accessToken?: string) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const mutate = async (payload: Record<string, unknown>) => {
    if (!accessToken) return null
    setSaving(true)
    setError('')
    try {
      return await updateRoomStatus(accessToken, payload)
    } catch (err: any) {
      setError(err.message || 'Failed to update room status.')
      throw err
    } finally {
      setSaving(false)
    }
  }

  return { mutate, saving, error }
}
