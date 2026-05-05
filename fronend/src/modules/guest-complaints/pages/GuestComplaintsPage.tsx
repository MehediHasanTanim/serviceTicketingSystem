import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useGuestComplaints } from '../hooks/useGuestComplaints'
import type { ComplaintListFilters } from '../types/guestComplaints.types'
import { isOverdue } from '../components/utils'

const baseFilters: ComplaintListFilters = { q: '', status: '', severity: '', category: '', source: '', property: '', department: '', assigned_to: '', escalated_to: '', date_from: '', date_to: '', page: 1, page_size: 10 }

export function GuestComplaintsPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const [filters, setFilters] = useState<ComplaintListFilters>({ ...baseFilters, ...Object.fromEntries(params.entries()), page: Number(params.get('page') || '1'), page_size: Number(params.get('page_size') || '10') })
  const { data, loading, error, reload } = useGuestComplaints(auth?.accessToken, auth?.user?.org_id, filters)

  useEffect(() => {
    const p = new URLSearchParams()
    Object.entries(filters).forEach(([k, v]) => { if (String(v)) p.set(k, String(v)) })
    setParams(p, { replace: true })
  }, [filters, setParams])

  const rows = data?.results || []
  const pages = Math.max(1, Math.ceil((data?.count || 0) / filters.page_size))

  return <div className="page full"><div className="glass panel">
    <div className="section-head"><h2>Guest Complaints</h2><button className="button" onClick={() => navigate('/guest-complaints/new')}>New Complaint</button></div>
    <div className="grid-form filters-grid">
      <input className="input" placeholder="Search number, guest, room, title" value={filters.q} onChange={(e) => setFilters((p) => ({ ...p, q: e.target.value, page: 1 }))} />
      <select className="input" value={filters.status} onChange={(e) => setFilters((p) => ({ ...p, status: e.target.value, page: 1 }))}><option value="">All status</option>{['NEW','TRIAGED','ASSIGNED','IN_PROGRESS','ESCALATED','RESOLVED','CONFIRMED','REOPENED','CLOSED','VOID'].map((s) => <option key={s} value={s}>{s}</option>)}</select>
      <select className="input" value={filters.severity} onChange={(e) => setFilters((p) => ({ ...p, severity: e.target.value, page: 1 }))}><option value="">All severity</option>{['LOW','MEDIUM','HIGH','CRITICAL'].map((s) => <option key={s} value={s}>{s}</option>)}</select>
      <input className="input" placeholder="Category" value={filters.category} onChange={(e) => setFilters((p) => ({ ...p, category: e.target.value, page: 1 }))} />
      <input className="input" placeholder="Source" value={filters.source} onChange={(e) => setFilters((p) => ({ ...p, source: e.target.value, page: 1 }))} />
      <input className="input" placeholder="Property" value={filters.property} onChange={(e) => setFilters((p) => ({ ...p, property: e.target.value, page: 1 }))} />
      <input className="input" placeholder="Department" value={filters.department} onChange={(e) => setFilters((p) => ({ ...p, department: e.target.value, page: 1 }))} />
      <input className="input" placeholder="Assigned to" value={filters.assigned_to} onChange={(e) => setFilters((p) => ({ ...p, assigned_to: e.target.value, page: 1 }))} />
      <input className="input" placeholder="Escalated to" value={filters.escalated_to} onChange={(e) => setFilters((p) => ({ ...p, escalated_to: e.target.value, page: 1 }))} />
      <input className="input" type="date" value={filters.date_from} onChange={(e) => setFilters((p) => ({ ...p, date_from: e.target.value, page: 1 }))} />
      <input className="input" type="date" value={filters.date_to} onChange={(e) => setFilters((p) => ({ ...p, date_to: e.target.value, page: 1 }))} />
    </div>
    {loading ? <p>Loading complaints...</p> : null}
    {error ? <div><p className="error-text">{error}</p><button className="button secondary small" onClick={reload}>Retry</button></div> : null}
    {!loading && !error && rows.length === 0 ? <p className="hint">No complaints found.</p> : null}
    {rows.length > 0 ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Complaint #</th><th>Guest</th><th>Room</th><th>Category</th><th>Severity</th><th>Status</th><th>Assigned</th><th>Escalated</th><th>Due</th><th>Created</th><th>Actions</th></tr></thead><tbody>
      {rows.map((row) => <tr key={row.id} onClick={() => navigate(`/guest-complaints/${row.id}`)}><td>{row.complaint_number}</td><td>{row.guest_name}</td><td>{row.room_id || '-'}</td><td>{row.category}</td><td><span className={`badge ${row.severity.toLowerCase()}`}>{row.severity}</span></td><td><span className="badge neutral">{row.status}</span></td><td>{row.assigned_to || '-'}</td><td>{row.escalated_to || '-'}</td><td>{row.due_at ? new Date(row.due_at).toLocaleString() : '-'}{isOverdue(row.due_at, row.status) ? ' (Overdue)' : ''}</td><td>{new Date(row.created_at).toLocaleDateString()}</td><td><button className="button secondary small" onClick={(e) => { e.stopPropagation(); navigate(`/guest-complaints/${row.id}/edit`) }}>Edit</button></td></tr>)}
    </tbody></table></div> : null}
    <div className="pagination-row"><button className="button secondary small" disabled={filters.page <= 1} onClick={() => setFilters((p) => ({ ...p, page: p.page - 1 }))}>Prev</button><span>Page {filters.page} of {pages}</span><button className="button secondary small" disabled={filters.page >= pages} onClick={() => setFilters((p) => ({ ...p, page: p.page + 1 }))}>Next</button></div>
  </div></div>
}
