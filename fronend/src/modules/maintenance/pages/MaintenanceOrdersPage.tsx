import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { createMaintenanceOrder } from '../api/maintenance.api'
import { MaintenanceOrderForm } from '../components/MaintenanceOrderForm'
import { useMaintenanceOrders } from '../hooks/useMaintenance'
import type { MaintenanceOrderFilters } from '../types/maintenance.types'

const baseFilters: MaintenanceOrderFilters = { q: '', task_type: '', status: '', priority: '', asset: '', room: '', property: '', department: '', assigned_to: '', date_from: '', date_to: '', page: 1, page_size: 10 }

export function MaintenanceOrdersPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [showCreate, setShowCreate] = useState(false)
  const [saving, setSaving] = useState(false)
  const [filters, setFilters] = useState<MaintenanceOrderFilters>({ ...baseFilters, q: searchParams.get('q') || '', page: Number(searchParams.get('page') || 1) })
  const { data, loading, error, reload } = useMaintenanceOrders(auth?.accessToken, auth?.user?.org_id, filters)

  useEffect(() => {
    const params = new URLSearchParams()
    if (filters.q) params.set('q', filters.q)
    params.set('page', String(filters.page))
    setSearchParams(params, { replace: true })
  }, [filters, setSearchParams])

  const onCreate = async (payload: Record<string, unknown>) => {
    if (!auth?.accessToken) return
    setSaving(true)
    try {
      await createMaintenanceOrder(auth.accessToken, payload)
      setShowCreate(false)
      await reload()
    } finally {
      setSaving(false)
    }
  }

  const rows = data?.results || []
  const pages = Math.max(1, Math.ceil((data?.count || 0) / filters.page_size))

  return (
    <div className="page full">
      <div className="glass panel">
        <div className="section-head">
          <h2>Maintenance Orders</h2>
          <button className="button" onClick={() => setShowCreate((v) => !v)}>{showCreate ? 'Close' : 'New Order'}</button>
        </div>
        {showCreate ? <MaintenanceOrderForm orgId={auth?.user?.org_id || 0} mode="create" onSubmit={onCreate} saving={saving} /> : null}

        <div className="grid-form filters-grid">
          <input className="input" placeholder="Search" value={filters.q} onChange={(e) => setFilters((p) => ({ ...p, q: e.target.value, page: 1 }))} />
          <select className="input" value={filters.task_type} onChange={(e) => setFilters((p) => ({ ...p, task_type: e.target.value, page: 1 }))}><option value="">Task Type</option><option value="CORRECTIVE">CORRECTIVE</option><option value="PREVENTIVE">PREVENTIVE</option></select>
          <select className="input" value={filters.status} onChange={(e) => setFilters((p) => ({ ...p, status: e.target.value, page: 1 }))}><option value="">Status</option><option value="OPEN">OPEN</option><option value="ASSIGNED">ASSIGNED</option><option value="IN_PROGRESS">IN_PROGRESS</option><option value="ON_HOLD">ON_HOLD</option><option value="COMPLETED">COMPLETED</option><option value="CANCELLED">CANCELLED</option><option value="VOID">VOID</option></select>
          <select className="input" value={filters.priority} onChange={(e) => setFilters((p) => ({ ...p, priority: e.target.value, page: 1 }))}><option value="">Priority</option><option value="LOW">LOW</option><option value="MEDIUM">MEDIUM</option><option value="HIGH">HIGH</option><option value="URGENT">URGENT</option></select>
        </div>

        {loading ? <p>Loading maintenance orders...</p> : null}
        {error ? <div><p className="error-text">{error}</p><button className="button secondary small" onClick={reload}>Retry</button></div> : null}
        {!loading && !error && rows.length === 0 ? <p className="hint">No maintenance tasks found.</p> : null}

        {rows.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead><tr><th>Task Number</th><th>Title</th><th>Type</th><th>Asset</th><th>Room</th><th>Priority</th><th>Status</th><th>Assigned To</th><th>Due Date</th><th>Updated At</th><th>Actions</th></tr></thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id} onClick={() => navigate(`/maintenance/orders/${row.id}`)}>
                    <td>{row.task_number}</td><td>{row.title}</td><td>{row.task_type}</td><td>{row.asset_id || '-'}</td><td>{row.room_id || '-'}</td>
                    <td><span className={`badge ${row.priority.toLowerCase()}`}>{row.priority}</span></td><td><span className="badge neutral">{row.status}</span></td><td>{row.assigned_to || '-'}</td>
                    <td>{row.due_at ? new Date(row.due_at).toLocaleString() : '-'}</td><td>{new Date(row.updated_at).toLocaleDateString()}</td>
                    <td><button className="button secondary small" onClick={(e) => { e.stopPropagation(); navigate(`/maintenance/orders/${row.id}/edit`) }}>Edit</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        <div className="pagination-row">
          <button className="button secondary small" disabled={filters.page <= 1} onClick={() => setFilters((p) => ({ ...p, page: p.page - 1 }))}>Prev</button>
          <span>Page {filters.page} of {pages}</span>
          <button className="button secondary small" disabled={filters.page >= pages} onClick={() => setFilters((p) => ({ ...p, page: p.page + 1 }))}>Next</button>
        </div>
      </div>
    </div>
  )
}
