import { useState } from 'react'
import { useAuth } from '../../../features/auth/authContext'
import { useFBAuditLogs } from '../hooks/useFoodBeverage'
import type { FBAuditFilters } from '../types/foodBeverage.types'

const base: FBAuditFilters = { date_from: '', date_to: '', actor_user_id: '', action: '', target_type: '', outlet_id: '', task_id: '', breakfast_count_id: '', readiness_id: '', page: 1, page_size: 10, sort_by: 'created_at', sort_dir: 'desc' }

export function FBAuditLogsPage() {
  const { auth } = useAuth(); const [filters, setFilters] = useState(base); const [active, setActive] = useState<number | null>(null)
  const { data, loading, error } = useFBAuditLogs(auth?.accessToken, auth?.user?.org_id, filters)
  const rows = data?.results || []; const pages = Math.max(1, Math.ceil((data?.count || 0) / filters.page_size))
  return <div className="page full"><div className="glass panel"><h2>F&B Audit Logs</h2>
    <div className="grid-form three"><input className="input" placeholder="Action" value={filters.action} onChange={(e) => setFilters((p) => ({ ...p, action: e.target.value, page: 1 }))} /><input className="input" placeholder="Entity Type" value={filters.target_type} onChange={(e) => setFilters((p) => ({ ...p, target_type: e.target.value, page: 1 }))} /><input className="input" placeholder="Actor ID" value={filters.actor_user_id} onChange={(e) => setFilters((p) => ({ ...p, actor_user_id: e.target.value, page: 1 }))} /></div>
    {loading ? <p>Loading logs...</p> : null}{error ? <p className="error-text">{error}</p> : null}
    <div className="table-wrap"><table className="data-table"><thead><tr><th>Timestamp</th><th>Actor</th><th>Action</th><th>Entity Type</th><th>Entity ID</th><th>Details</th></tr></thead><tbody>{rows.map((r) => <tr key={r.id}><td>{new Date(r.created_at).toLocaleString()}</td><td>{r.actor_user_id || 'System'}</td><td>{r.action}</td><td>{r.target_type}</td><td>{r.target_id}</td><td><button className="button secondary small" onClick={() => setActive(r.id)}>Open</button></td></tr>)}</tbody></table></div>
    <div className="pagination-row"><button className="button secondary small" disabled={filters.page <= 1} onClick={() => setFilters((p) => ({ ...p, page: p.page - 1 }))}>Prev</button><span>Page {filters.page} of {pages}</span><button className="button secondary small" disabled={filters.page >= pages} onClick={() => setFilters((p) => ({ ...p, page: p.page + 1 }))}>Next</button></div>
    {active ? <div className="modal-backdrop" role="presentation"><div className="modal" role="dialog" aria-modal="true" aria-label="Audit metadata"><pre>{JSON.stringify(rows.find((r) => r.id === active)?.metadata || {}, null, 2)}</pre><div className="modal-actions"><button className="button secondary small" onClick={() => setActive(null)}>Close</button></div></div></div> : null}
  </div></div>
}
