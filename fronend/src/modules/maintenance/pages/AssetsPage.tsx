import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { createAsset } from '../api/maintenance.api'
import { useAssets } from '../hooks/useMaintenance'
import type { AssetFilters } from '../types/maintenance.types'

const base: AssetFilters = { q: '', status: '', category: '', location: '', room: '', department: '', property: '', criticality: '', warranty_expiring_before: '', page: 1, page_size: 10 }

export function AssetsPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const [filters, setFilters] = useState<AssetFilters>(base)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ asset_code: '', qr_code: '', name: '', purchase_date: '', warranty_expiry_date: '', status: 'ACTIVE', criticality: 'MEDIUM' })
  const [error, setError] = useState('')
  const { data, loading, error: loadError, reload } = useAssets(auth?.accessToken, auth?.user?.org_id, filters)

  const save = async () => {
    if (!auth?.accessToken || !auth.user?.org_id) return
    setError('')
    if (form.purchase_date && form.warranty_expiry_date && form.purchase_date > form.warranty_expiry_date) {
      setError('Warranty expiry must be after purchase date.')
      return
    }
    try {
      await createAsset(auth.accessToken, { org_id: auth.user.org_id, ...form, qr_code: form.qr_code || null })
      setShowCreate(false)
      await reload()
    } catch (err: any) {
      setError(err.message || 'Failed to create asset')
    }
  }

  const rows = data?.results || []
  return <div className="page full"><div className="glass panel"><div className="section-head"><h2>Assets</h2><button className="button" onClick={() => setShowCreate((v) => !v)}>{showCreate ? 'Close' : 'New Asset'}</button></div>
    {showCreate ? <div className="card-section"><div className="grid-form three"><input className="input" placeholder="Asset Code" value={form.asset_code} onChange={(e) => setForm((p) => ({ ...p, asset_code: e.target.value }))} /><input className="input" placeholder="QR Code" value={form.qr_code} onChange={(e) => setForm((p) => ({ ...p, qr_code: e.target.value }))} /><input className="input" placeholder="Name" value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))} /><input className="input" type="date" value={form.purchase_date} onChange={(e) => setForm((p) => ({ ...p, purchase_date: e.target.value }))} /><input className="input" type="date" value={form.warranty_expiry_date} onChange={(e) => setForm((p) => ({ ...p, warranty_expiry_date: e.target.value }))} /></div><button className="button" onClick={save}>Save</button>{error ? <p className="error-text">{error}</p> : null}</div> : null}
    <input className="input" placeholder="Search assets" value={filters.q} onChange={(e) => setFilters((p) => ({ ...p, q: e.target.value }))} />
    {loading ? <p>Loading...</p> : null}{loadError ? <p className="error-text">{loadError}</p> : null}
    <div className="table-wrap"><table className="data-table"><thead><tr><th>Asset Code</th><th>QR</th><th>Name</th><th>Status</th><th>Criticality</th><th>Warranty Expiry</th><th>Updated</th><th>Actions</th></tr></thead><tbody>{rows.map((row) => <tr key={row.id}><td>{row.asset_code}</td><td>{row.qr_code || '-'}</td><td>{row.name}</td><td>{row.status}</td><td>{row.criticality}</td><td>{row.warranty_expiry_date || '-'}</td><td>{new Date(row.updated_at).toLocaleDateString()}</td><td><button className="button secondary small" onClick={() => navigate(`/maintenance/assets/${row.id}`)}>Open</button></td></tr>)}</tbody></table></div>
  </div></div>
}
