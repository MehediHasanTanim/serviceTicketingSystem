import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useBreakfastCounts } from '../hooks/useFoodBeverage'
import type { BreakfastCountFilters } from '../types/foodBeverage.types'

const base: BreakfastCountFilters = { property_id: '', outlet_id: '', date_from: '', date_to: '', q: '', sort_by: 'updated_at', sort_dir: 'desc', page: 1, page_size: 10 }

export function BreakfastCountsPage() {
  const { auth } = useAuth(); const navigate = useNavigate(); const [params, setParams] = useSearchParams()
  const [filters, setFilters] = useState<BreakfastCountFilters>({ ...base, page: Number(params.get('page') || 1), q: params.get('q') || '' })
  const { data, loading, error, reload } = useBreakfastCounts(auth?.accessToken, auth?.user?.org_id, filters)
  useEffect(() => { const p = new URLSearchParams(); if (filters.q) p.set('q', filters.q); p.set('page', String(filters.page)); setParams(p, { replace: true }) }, [filters, setParams])
  const rows = data?.results || []; const pages = Math.max(1, Math.ceil((data?.count || 0) / filters.page_size))

  return <div className="page full"><div className="glass panel"><div className="section-head"><h2>Breakfast Counts</h2><button className="button" onClick={() => navigate('/food-beverage/breakfast-counts/new')}>New Breakfast Count</button></div>
    <div className="grid-form filters-grid"><input className="input" placeholder="Search" value={filters.q} onChange={(e) => setFilters((p) => ({ ...p, q: e.target.value, page: 1 }))} /><input className="input" placeholder="Property ID" value={filters.property_id} onChange={(e) => setFilters((p) => ({ ...p, property_id: e.target.value, page: 1 }))} /><input className="input" placeholder="Outlet ID" value={filters.outlet_id} onChange={(e) => setFilters((p) => ({ ...p, outlet_id: e.target.value, page: 1 }))} /><input className="input" type="date" value={filters.date_from} onChange={(e) => setFilters((p) => ({ ...p, date_from: e.target.value, page: 1 }))} /><input className="input" type="date" value={filters.date_to} onChange={(e) => setFilters((p) => ({ ...p, date_to: e.target.value, page: 1 }))} /></div>
    {loading ? <p>Loading breakfast counts...</p> : null}{error ? <div><p className="error-text">{error}</p><button className="button secondary small" onClick={reload}>Retry</button></div> : null}
    {!loading && !error && rows.length === 0 ? <p className="hint">No breakfast counts found.</p> : null}
    {rows.length > 0 ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Service Date</th><th>Property</th><th>Outlet</th><th>Expected</th><th>Actual</th><th>Variance</th><th>Complimentary</th><th>Paid</th><th>No-show</th><th>Recorded By</th><th>Updated</th><th>Actions</th></tr></thead><tbody>{rows.map((r) => { const variance = (r.actual_guest_count || 0) - (r.expected_guest_count || 0); const cls = variance === 0 ? 'neutral' : variance > 0 ? 'warning' : 'critical'; return <tr key={r.id}><td>{r.service_date}</td><td>{r.property_id}</td><td>{r.outlet_id}</td><td>{r.expected_guest_count}</td><td>{r.actual_guest_count}</td><td><span className={`badge ${cls}`}>{variance}</span></td><td>{r.complimentary_count}</td><td>{r.paid_count}</td><td>{r.no_show_count}</td><td>{r.recorded_by || '-'}</td><td>{new Date(r.updated_at).toLocaleString()}</td><td><button className="button secondary small" onClick={() => navigate(`/food-beverage/breakfast-counts/${r.id}`)}>Open</button></td></tr> })}</tbody></table></div> : null}
    <div className="pagination-row"><button className="button secondary small" disabled={filters.page <= 1} onClick={() => setFilters((p) => ({ ...p, page: p.page - 1 }))}>Prev</button><span>Page {filters.page} of {pages}</span><button className="button secondary small" disabled={filters.page >= pages} onClick={() => setFilters((p) => ({ ...p, page: p.page + 1 }))}>Next</button></div>
  </div></div>
}
