import { useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { createMaintenanceOrder, updateMaintenanceOrder } from '../api/maintenance.api'
import { MaintenanceOrderForm } from '../components/MaintenanceOrderForm'
import { useMaintenanceOrderDetail } from '../hooks/useMaintenance'

export function MaintenanceOrderFormPage() {
  const { id } = useParams()
  const editingId = id ? Number(id) : null
  const [query] = useSearchParams()
  const prefilledAssetId = Number(query.get('asset_id') || '') || null
  const { auth } = useAuth()
  const navigate = useNavigate()
  const [saving, setSaving] = useState(false)
  const detail = useMaintenanceOrderDetail(auth?.accessToken, auth?.user?.org_id, editingId || undefined)

  const onSubmit = async (payload: Record<string, unknown>) => {
    if (!auth?.accessToken) return
    setSaving(true)
    try {
      if (editingId) {
        await updateMaintenanceOrder(auth.accessToken, editingId, payload)
        navigate(`/maintenance/orders/${editingId}`)
      } else {
        const created = await createMaintenanceOrder(auth.accessToken, payload)
        navigate(`/maintenance/orders/${created.id}`)
      }
    } finally {
      setSaving(false)
    }
  }

  return <div className="page full"><div className="glass panel"><h2>{editingId ? 'Edit Maintenance Order' : 'Create Maintenance Order'}</h2><MaintenanceOrderForm orgId={auth?.user?.org_id || 0} mode={editingId ? 'edit' : 'create'} initial={detail.data} prefilledAssetId={prefilledAssetId} onSubmit={onSubmit} saving={saving} /></div></div>
}
