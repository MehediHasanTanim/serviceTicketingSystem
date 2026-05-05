import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { getGuestComplaint } from '../api/guestComplaints.api'
import { ComplaintForm } from '../components/ComplaintForm'
import { useCreateGuestComplaint, useUpdateGuestComplaint } from '../hooks/useGuestComplaints'
import type { GuestComplaint } from '../types/guestComplaints.types'
import { useEffect } from 'react'

export function GuestComplaintFormPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const params = useParams()
  const complaintId = Number(params.id)
  const editMode = Number.isFinite(complaintId) && complaintId > 0
  const [initial, setInitial] = useState<GuestComplaint | undefined>()
  const [loading, setLoading] = useState(editMode)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const create = useCreateGuestComplaint()
  const update = useUpdateGuestComplaint()

  useEffect(() => {
    if (!editMode || !auth?.accessToken || !auth.user?.org_id) return
    ;(async () => {
      try { setInitial(await getGuestComplaint(auth.accessToken, auth.user?.org_id || 0, complaintId)) } catch (err: any) { setError(err.message || 'Failed to load complaint') } finally { setLoading(false) }
    })()
  }, [editMode, auth?.accessToken, auth?.user?.org_id, complaintId])

  const submit = async (payload: Record<string, unknown>) => {
    if (!auth?.accessToken) return
    setSaving(true)
    setError('')
    try {
      if (editMode) await update(auth.accessToken, complaintId, payload)
      else await create(auth.accessToken, payload)
      navigate('/guest-complaints')
    } catch (err: any) {
      setError(err.message || 'Request failed')
    } finally {
      setSaving(false)
    }
  }

  return <div className="page full"><div className="glass panel">{loading ? <p>Loading complaint...</p> : <ComplaintForm orgId={auth?.user?.org_id || 0} mode={editMode ? 'edit' : 'create'} initial={initial} onSubmit={submit} saving={saving} apiError={error} />}</div></div>
}
