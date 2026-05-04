import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../auth/authContext'
import { fetchServiceOrders, createServiceOrder } from './api'
import { OrderForm } from './components/OrderForm'
import type { ServiceOrder, ServiceOrderFilters } from './types'
import { formatCurrency } from './utils'

const baseFilters: ServiceOrderFilters = {
  q: '', status: '', priority: '', type: '', assigned_to: '', customer_id: '', date_from: '', date_to: '',
  page: 1, page_size: 10, sort_by: 'updated_at', sort_dir: 'desc',
}

export function ServiceOrdersPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [filters, setFilters] = useState<ServiceOrderFilters>(() => ({
    ...baseFilters,
    q: searchParams.get('q') || '',
    status: searchParams.get('status') || '',
    priority: searchParams.get('priority') || '',
    type: searchParams.get('type') || '',
    assigned_to: searchParams.get('assigned_to') || '',
    customer_id: searchParams.get('customer_id') || '',
    date_from: searchParams.get('date_from') || '',
    date_to: searchParams.get('date_to') || '',
    page: Number(searchParams.get('page') || '1'),
    page_size: Number(searchParams.get('page_size') || '10'),
    sort_by: searchParams.get('sort_by') || 'updated_at',
    sort_dir: (searchParams.get('sort_dir') as 'asc' | 'desc') || 'desc',
  }))
  const [searchInput, setSearchInput] = useState(searchParams.get('q') || '')
  const [rows, setRows] = useState<ServiceOrder[]>([])
  const [count, setCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [showCreate, setShowCreate] = useState(false)

  useEffect(() => {
    const timeout = setTimeout(() => {
      setFilters((prev) => ({ ...prev, q: searchInput, page: 1 }))
    }, 300)
    return () => clearTimeout(timeout)
  }, [searchInput])

  useEffect(() => {
    const params = new URLSearchParams()
    params.set('page', String(filters.page))
    params.set('page_size', String(filters.page_size))
    params.set('sort_by', filters.sort_by)
    params.set('sort_dir', filters.sort_dir)
    if (filters.q) params.set('q', filters.q)
    if (filters.status) params.set('status', filters.status)
    if (filters.priority) params.set('priority', filters.priority)
    if (filters.type) params.set('type', filters.type)
    if (filters.assigned_to) params.set('assigned_to', filters.assigned_to)
    if (filters.customer_id) params.set('customer_id', filters.customer_id)
    if (filters.date_from) params.set('date_from', filters.date_from)
    if (filters.date_to) params.set('date_to', filters.date_to)
    setSearchParams(params, { replace: true })
  }, [filters, setSearchParams])

  const load = async () => {
    if (!auth?.accessToken || !auth.user?.org_id) return
    setLoading(true)
    setError('')
    try {
      const data = await fetchServiceOrders(auth.accessToken, auth.user.org_id, filters)
      setRows(data.results)
      setCount(data.count)
    } catch (err: any) {
      setError(err.message || 'Failed to load service orders.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [auth?.accessToken, auth?.user?.org_id, filters.page, filters.page_size, filters.sort_by, filters.sort_dir, filters.q, filters.status, filters.priority, filters.type, filters.assigned_to, filters.customer_id, filters.date_from, filters.date_to])

  const pages = Math.max(1, Math.ceil(count / filters.page_size))
  const users = useMemo(() => [], [])
  const onSort = (field: string) => {
    setFilters((prev) => ({
      ...prev,
      sort_by: field,
      sort_dir: prev.sort_by === field && prev.sort_dir === 'asc' ? 'desc' : 'asc',
      page: 1,
    }))
  }
  const sortMark = (field: string) => (filters.sort_by === field ? (filters.sort_dir === 'asc' ? '▲' : '▼') : '')

  const onCreate = async (payload: Record<string, unknown>) => {
    if (!auth?.accessToken) return
    setSaving(true)
    try {
      await createServiceOrder(auth.accessToken, payload)
      setShowCreate(false)
      await load()
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="page full">
      <div className="glass panel">
        <div className="section-head">
          <h2>Service Orders</h2>
          <button className="button" onClick={() => setShowCreate((v) => !v)}>{showCreate ? 'Close' : 'Create Order'}</button>
        </div>
        {showCreate ? <OrderForm orgId={auth?.user?.org_id || 0} mode="create" users={users} onSubmit={onCreate} saving={saving} /> : null}

        <div className="grid-form filters-grid">
          <input className="input" placeholder="Search by title or ticket" value={searchInput} onChange={(e) => setSearchInput(e.target.value)} />
          <select className="input" value={filters.status} onChange={(e) => setFilters((p) => ({ ...p, status: e.target.value, page: 1 }))}>
            <option value="">All Status</option><option value="OPEN">OPEN</option><option value="ASSIGNED">ASSIGNED</option><option value="IN_PROGRESS">IN_PROGRESS</option><option value="ON_HOLD">ON_HOLD</option><option value="DEFERRED">DEFERRED</option><option value="COMPLETED">COMPLETED</option><option value="VOID">VOID</option>
          </select>
          <select className="input" value={filters.priority} onChange={(e) => setFilters((p) => ({ ...p, priority: e.target.value, page: 1 }))}>
            <option value="">All Priority</option><option value="LOW">LOW</option><option value="MEDIUM">MEDIUM</option><option value="HIGH">HIGH</option><option value="URGENT">URGENT</option>
          </select>
          <select className="input" value={filters.type} onChange={(e) => setFilters((p) => ({ ...p, type: e.target.value, page: 1 }))}>
            <option value="">All Type</option><option value="INSTALLATION">INSTALLATION</option><option value="REPAIR">REPAIR</option><option value="MAINTENANCE">MAINTENANCE</option><option value="INSPECTION">INSPECTION</option><option value="OTHER">OTHER</option>
          </select>
          <input className="input" placeholder="Assigned user ID" value={filters.assigned_to} onChange={(e) => setFilters((p) => ({ ...p, assigned_to: e.target.value, page: 1 }))} />
          <input className="input" placeholder="Customer ID" value={filters.customer_id} onChange={(e) => setFilters((p) => ({ ...p, customer_id: e.target.value, page: 1 }))} />
          <input className="input" type="date" value={filters.date_from} onChange={(e) => setFilters((p) => ({ ...p, date_from: e.target.value, page: 1 }))} />
          <input className="input" type="date" value={filters.date_to} onChange={(e) => setFilters((p) => ({ ...p, date_to: e.target.value, page: 1 }))} />
        </div>

        {loading ? (
          <div className="table-wrap" aria-label="Loading skeleton">
            <table className="data-table">
              <tbody>
                {Array.from({ length: 5 }).map((_, idx) => (
                  <tr key={idx} className="skeleton-row">
                    {Array.from({ length: 11 }).map((__, col) => (
                      <td key={col}><span className="skeleton-block" /></td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
        {error ? <div><p className="error-text">{error}</p><button className="button secondary small" onClick={load}>Retry</button></div> : null}
        {!loading && !error && rows.length === 0 ? <p className="hint">No service orders found.</p> : null}

        {rows.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table" aria-label="Service orders table">
              <thead>
                <tr>
                  <th><button className="header-button" onClick={() => onSort('ticket_number')}>Ticket Number {sortMark('ticket_number')}</button></th>
                  <th><button className="header-button" onClick={() => onSort('title')}>Title {sortMark('title')}</button></th>
                  <th>Customer</th><th>Assigned To</th>
                  <th><button className="header-button" onClick={() => onSort('priority')}>Priority {sortMark('priority')}</button></th>
                  <th><button className="header-button" onClick={() => onSort('type')}>Type {sortMark('type')}</button></th>
                  <th><button className="header-button" onClick={() => onSort('status')}>Status {sortMark('status')}</button></th>
                  <th><button className="header-button" onClick={() => onSort('due_date')}>Due Date {sortMark('due_date')}</button></th>
                  <th><button className="header-button" onClick={() => onSort('total_cost')}>Total Cost {sortMark('total_cost')}</button></th>
                  <th><button className="header-button" onClick={() => onSort('updated_at')}>Updated At {sortMark('updated_at')}</button></th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id} onClick={() => navigate(`/service-orders/${row.id}`)}>
                    <td>{row.ticket_number}</td>
                    <td>{row.title}</td>
                    <td>#{row.customer_id}</td>
                    <td>{row.assigned_to ? `#${row.assigned_to}` : 'Unassigned'}</td>
                    <td><span className={`badge ${row.priority.toLowerCase()}`}>{row.priority}</span></td>
                    <td>{row.type}</td>
                    <td><span className="badge neutral">{row.status}</span></td>
                    <td>{row.due_date || '-'}</td>
                    <td>{formatCurrency(row.total_cost)}</td>
                    <td>{new Date(row.updated_at).toLocaleDateString()}</td>
                    <td>
                      <select
                        className="input"
                        aria-label={`Actions for ${row.ticket_number}`}
                        defaultValue=""
                        onClick={(e) => e.stopPropagation()}
                        onChange={(e) => {
                          if (e.target.value === 'open') navigate(`/service-orders/${row.id}`)
                          if (e.target.value === 'edit') navigate(`/service-orders/${row.id}?edit=1`)
                        }}
                      >
                        <option value="">Select</option>
                        <option value="open">Open</option>
                        <option value="edit">Open in edit</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        <div className="pagination-row">
          <button className="button secondary small" disabled={filters.page <= 1} onClick={() => setFilters((p) => ({ ...p, page: p.page - 1 }))}>Prev</button>
          <span>Page {filters.page} of {pages}</span>
          <select className="input page-size-select" value={filters.page_size} onChange={(e) => setFilters((p) => ({ ...p, page_size: Number(e.target.value), page: 1 }))}>
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
          </select>
          <button className="button secondary small" disabled={filters.page >= pages} onClick={() => setFilters((p) => ({ ...p, page: p.page + 1 }))}>Next</button>
        </div>
      </div>
    </div>
  )
}
