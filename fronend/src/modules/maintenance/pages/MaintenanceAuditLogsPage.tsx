import { useState } from 'react'
import { useAuth } from '../../../features/auth/authContext'
import { useMaintenanceAuditLogs } from '../hooks/useMaintenance'
import type { AuditLogFilters } from '../types/maintenance.types'

const base: AuditLogFilters = { q: '', property_id: '', actor_user_id: '', action: '', target_type: '', target_id: '', date_from: '', date_to: '', page: 1, page_size: 10, sort_by: 'created_at', sort_dir: 'desc' }

export function MaintenanceAuditLogsPage() {
  const { auth } = useAuth()
  const [filters, setFilters] = useState<AuditLogFilters>(base)
  const [activeMeta, setActiveMeta] = useState<Record<string, unknown> | null>(null)
  const { data, loading, error } = useMaintenanceAuditLogs(auth?.accessToken, auth?.user?.org_id, filters)
  const pages = Math.max(1, Math.ceil((data?.count || 0) / filters.page_size))

  return <div className="page full"><div className="glass panel"><h2>Maintenance Audit Logs</h2>
    <div className="grid-form three"><input className="input" placeholder="Action" value={filters.action} onChange={(e) => setFilters((p) => ({ ...p, action: e.target.value, page: 1 }))} /><input className="input" placeholder="Entity Type" value={filters.target_type} onChange={(e) => setFilters((p) => ({ ...p, target_type: e.target.value, page: 1 }))} /><input className="input" placeholder="Actor ID" value={filters.actor_user_id} onChange={(e) => setFilters((p) => ({ ...p, actor_user_id: e.target.value, page: 1 }))} /></div>
    {loading ? <p>Loading logs...</p> : null}{error ? <p className="error-text">{error}</p> : null}
    <div className="table-wrap"><table className="data-table"><thead><tr><th>Timestamp</th><th>Actor</th><th>Action</th><th>Entity</th><th>ID</th><th>Details</th></tr></thead><tbody>{(data?.results || []).map((row) => <tr key={row.id}><td>{new Date(row.created_at).toLocaleString()}</td><td>{row.actor_user_id || 'System'}</td><td>{row.action}</td><td>{row.target_type}</td><td>{row.target_id}</td><td><button className="button secondary small" onClick={() => setActiveMeta(row.metadata)}>Open</button></td></tr>)}</tbody></table></div>
    <div className="pagination-row"><button className="button secondary small" disabled={filters.page <= 1} onClick={() => setFilters((p) => ({ ...p, page: p.page - 1 }))}>Prev</button><span>Page {filters.page} of {pages}</span><button className="button secondary small" disabled={filters.page >= pages} onClick={() => setFilters((p) => ({ ...p, page: p.page + 1 }))}>Next</button></div>
    {activeMeta ? <div className="card-section"><h3>Metadata</h3><pre>{JSON.stringify(activeMeta, null, 2)}</pre><button className="button secondary small" onClick={() => setActiveMeta(null)}>Close</button></div> : null}
  </div></div>
}
