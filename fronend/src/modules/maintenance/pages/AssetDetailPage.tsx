import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { transitionAssetStatus, updateAsset } from '../api/maintenance.api'
import { useAssetDetail } from '../hooks/useMaintenance'

export function AssetDetailPage() {
  const { id } = useParams()
  const assetId = Number(id)
  const navigate = useNavigate()
  const { auth } = useAuth()
  const { data, loading, error, reload } = useAssetDetail(auth?.accessToken, auth?.user?.org_id, assetId)
  const [busy, setBusy] = useState(false)

  if (loading) return <div className="page full"><div className="glass panel"><p>Loading asset...</p></div></div>
  if (error || !data) return <div className="page full"><div className="glass panel"><p className="error-text">{error || 'Asset not found'}</p></div></div>

  const doStatus = async () => {
    if (!auth?.accessToken || !auth.user?.org_id) return
    const newStatus = prompt('New status (ACTIVE/INACTIVE/UNDER_MAINTENANCE/OUT_OF_SERVICE/RETIRED)')
    if (!newStatus) return
    const reason = prompt('Reason') || ''
    setBusy(true)
    try {
      await transitionAssetStatus(auth.accessToken, assetId, { org_id: auth.user.org_id, new_status: newStatus, reason })
      await reload()
    } finally {
      setBusy(false)
    }
  }

  return <div className="page full"><div className="glass panel"><div className="section-head"><h2>{data.asset.asset_code} • {data.asset.name}</h2><button className="button secondary" onClick={() => navigate(`/maintenance/assets/${assetId}/edit`)}>Edit</button></div>
    <p>Status: <span className="badge neutral">{data.asset.status}</span></p>
    <p>{data.asset.description || 'No description.'}</p>
    <button className="button" disabled={busy} onClick={doStatus}>Status Transition</button>
    <h3>Lifecycle History</h3>
    <ul className="simple-list">{data.history.map((row) => <li key={row.id}>{new Date(row.changed_at).toLocaleString()} • {row.previous_status} → {row.new_status} • {row.reason || 'N/A'}</li>)}</ul>
  </div></div>
}

export function AssetEditPage() {
  const { id } = useParams()
  const assetId = Number(id)
  const { auth } = useAuth()
  const navigate = useNavigate()
  const { data, loading } = useAssetDetail(auth?.accessToken, auth?.user?.org_id, assetId)
  const [name, setName] = useState('')

  if (loading || !data) return <div className="page full"><div className="glass panel"><p>Loading...</p></div></div>

  const onSave = async () => {
    if (!auth?.accessToken || !auth.user?.org_id) return
    await updateAsset(auth.accessToken, assetId, { org_id: auth.user.org_id, name: name || data.asset.name })
    navigate(`/maintenance/assets/${assetId}`)
  }

  return <div className="page full"><div className="glass panel"><h2>Edit Asset</h2><input className="input" defaultValue={data.asset.name} onChange={(e) => setName(e.target.value)} /><button className="button" onClick={onSave}>Save</button></div></div>
}
