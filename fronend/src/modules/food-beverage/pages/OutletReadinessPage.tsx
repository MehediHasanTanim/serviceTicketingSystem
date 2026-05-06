import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useOutletReadiness } from '../hooks/useFoodBeverage'
import type { OutletReadinessFilters } from '../types/foodBeverage.types'

const base: OutletReadinessFilters = { property_id: '', outlet_id: '', shift: '', status: '', date_from: '', date_to: '', page: 1, page_size: 10 }

export function OutletReadinessPage() {
  const { auth } = useAuth(); const navigate = useNavigate(); const [filters, setFilters] = useState(base)
  const { data, loading, error } = useOutletReadiness(auth?.accessToken, auth?.user?.org_id, filters)
  const rows = data?.results || []
  return <div className="page full"><div className="glass panel"><h2>Outlet Readiness</h2>
    <div className="grid-form filters-grid"><input className="input" placeholder="Property ID" value={filters.property_id} onChange={(e) => setFilters((p) => ({ ...p, property_id: e.target.value, page: 1 }))} /><input className="input" placeholder="Outlet ID" value={filters.outlet_id} onChange={(e) => setFilters((p) => ({ ...p, outlet_id: e.target.value, page: 1 }))} /><select className="input" value={filters.shift} onChange={(e) => setFilters((p) => ({ ...p, shift: e.target.value, page: 1 }))}><option value="">Shift</option><option value="BREAKFAST">BREAKFAST</option><option value="LUNCH">LUNCH</option><option value="DINNER">DINNER</option></select><select className="input" value={filters.status} onChange={(e) => setFilters((p) => ({ ...p, status: e.target.value, page: 1 }))}><option value="">Status</option>{['PENDING','IN_PROGRESS','READY','NOT_READY','VERIFIED','VOID'].map((s)=><option key={s} value={s}>{s}</option>)}</select></div>
    {loading ? <p>Loading...</p> : null}{error ? <p className="error-text">{error}</p> : null}
    <div className="table-wrap"><table className="data-table"><thead><tr><th>Readiness Date</th><th>Property</th><th>Outlet</th><th>Shift</th><th>Status</th><th>Checklist Score</th><th>Verified By</th><th>Verified At</th><th>Updated At</th><th>Actions</th></tr></thead><tbody>{rows.map((r) => <tr key={r.id}><td>{r.readiness_date}</td><td>{r.property_id}</td><td>{r.outlet_id}</td><td>{r.shift}</td><td><span className="badge neutral">{r.status}</span></td><td>{r.checklist_score}</td><td>{r.verified_by || '-'}</td><td>{r.verified_at ? new Date(r.verified_at).toLocaleString() : '-'}</td><td>{new Date(r.updated_at).toLocaleString()}</td><td><button className="button secondary small" onClick={() => navigate(`/food-beverage/outlet-readiness/${r.id}`)}>Open</button></td></tr>)}</tbody></table></div>
  </div></div>
}
