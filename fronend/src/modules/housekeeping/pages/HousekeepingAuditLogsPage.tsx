import { useMemo, useState } from 'react'
import { useAuth } from '../../../features/auth/authContext'
import { useHousekeepingAuditLogs, type HousekeepingAuditFilters } from '../hooks/useHousekeepingAuditLogs'

const base: Omit<HousekeepingAuditFilters, 'org_id'> = {
  q: '', actor_user_id: '', action: '', target_type: 'housekeeping', target_id: '', date_from: '', date_to: '',
  page: 1, page_size: 10, sort_by: 'created_at', sort_dir: 'desc',
}

export function HousekeepingAuditLogsPage() {
  const { auth } = useAuth()
  const [filters, setFilters] = useState(base)
  const query = useMemo(() => ({ ...filters, org_id: auth?.user?.org_id || 0 }), [filters, auth?.user?.org_id])
  const { rows, count, loading, error, reload } = useHousekeepingAuditLogs(auth?.accessToken, query)
  const [active, setActive] = useState<number | null>(null)
  const pages = Math.max(1, Math.ceil(count / filters.page_size))

  return <div className="page full"><div className="glass panel"><div className="section-head"><h2>Housekeeping Audit Logs</h2><button className="button secondary small" onClick={reload}>Refresh</button></div>
    <div className="grid-form filters-grid"><input className="input" placeholder="Search" value={filters.q} onChange={(e) => setFilters((p) => ({ ...p, q: e.target.value, page: 1 }))} /><input className="input" placeholder="Actor" value={filters.actor_user_id} onChange={(e) => setFilters((p) => ({ ...p, actor_user_id: e.target.value, page: 1 }))} /><input className="input" placeholder="Action" value={filters.action} onChange={(e) => setFilters((p) => ({ ...p, action: e.target.value, page: 1 }))} /></div>
    {loading ? <p className="helper">Loading audit logs...</p> : null}
    {error ? <p className="error">{error}</p> : null}
    <div className="table-wrap"><table className="data-table"><thead><tr><th><button className="header-button" onClick={() => setFilters((p) => ({ ...p, sort_by: 'created_at', sort_dir: p.sort_by === 'created_at' && p.sort_dir === 'asc' ? 'desc' : 'asc' }))}>Timestamp</button></th><th>Actor</th><th>Action</th><th>Entity</th><th>ID</th><th>Details</th></tr></thead><tbody>{rows.map((r) => <tr key={r.id}><td>{new Date(r.created_at).toLocaleString()}</td><td>{r.actor_user_id ?? '-'}</td><td>{r.action}</td><td>{r.target_type}</td><td>{r.target_id}</td><td><button className="button secondary small" onClick={() => setActive(r.id)}>Open</button></td></tr>)}</tbody></table></div>
    <div className="pagination-row"><button className="button secondary small" disabled={filters.page <= 1} onClick={() => setFilters((p) => ({ ...p, page: p.page - 1 }))}>Prev</button><span>Page {filters.page} of {pages}</span><button className="button secondary small" disabled={filters.page >= pages} onClick={() => setFilters((p) => ({ ...p, page: p.page + 1 }))}>Next</button></div>
    {active ? <div className="modal-backdrop" role="presentation"><div className="modal" role="dialog" aria-modal="true" aria-label="Audit metadata"><pre>{JSON.stringify(rows.find((r) => r.id === active)?.metadata || {}, null, 2)}</pre><div className="modal-actions"><button className="button secondary small" onClick={() => setActive(null)}>Close</button></div></div></div> : null}
  </div></div>
}
