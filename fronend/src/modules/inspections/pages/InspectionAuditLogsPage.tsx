import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useInspectionAuditLogs } from '../hooks/useInspections'
import type { InspectionAuditLogFilters } from '../types/inspections.types'

export function InspectionAuditLogsPage() {
  const { auth } = useAuth()
  const [params, setParams] = useSearchParams()
  const [filters, setFilters] = useState<InspectionAuditLogFilters>({ q: params.get('q') || '', actor_user_id: params.get('actor_user_id') || '', action: params.get('action') || 'inspection_', target_type: params.get('target_type') || '', target_id: params.get('target_id') || '', date_from: params.get('date_from') || '', date_to: params.get('date_to') || '', page: Number(params.get('page') || 1), page_size: 20, sort_by: 'created_at', sort_dir: 'desc' })
  const [activeMeta, setActiveMeta] = useState<Record<string, unknown> | null>(null)
  const { data, loading, error } = useInspectionAuditLogs(auth?.accessToken, auth?.user?.org_id, filters)

  const pages = Math.max(1, Math.ceil((data?.count || 0) / filters.page_size))
  const syncParams = (next: InspectionAuditLogFilters) => {
    const p = new URLSearchParams()
    Object.entries(next).forEach(([k, v]) => { if (v && String(v).length > 0) p.set(k, String(v)) })
    setParams(p, { replace: true })
    setFilters(next)
  }

  return <div className="page full"><div className="glass panel"><h2>Inspection Audit Logs</h2>
    <div className="grid-form three"><input className="input" placeholder="Action" value={filters.action} onChange={(e) => syncParams({ ...filters, action: e.target.value, page: 1 })} /><input className="input" placeholder="Entity type" value={filters.target_type} onChange={(e) => syncParams({ ...filters, target_type: e.target.value, page: 1 })} /><input className="input" placeholder="Actor ID" value={filters.actor_user_id} onChange={(e) => syncParams({ ...filters, actor_user_id: e.target.value, page: 1 })} /></div>
    {loading ? <p>Loading logs...</p> : null}{error ? <p className="error-text">{error}</p> : null}
    <div className="table-wrap"><table className="data-table"><thead><tr><th>Timestamp</th><th>Actor</th><th>Action</th><th>Entity Type</th><th>Entity ID</th><th>Metadata</th></tr></thead><tbody>{(data?.results || []).map((row) => <tr key={row.id}><td>{new Date(row.created_at).toLocaleString()}</td><td>{row.actor_user_id || 'System'}</td><td>{row.action}</td><td>{row.target_type}</td><td>{row.target_id}</td><td><button className="button secondary small" onClick={() => setActiveMeta(row.metadata)}>Open</button></td></tr>)}</tbody></table></div>
    <div className="pagination-row"><button className="button secondary small" disabled={filters.page <= 1} onClick={() => syncParams({ ...filters, page: filters.page - 1 })}>Prev</button><span>Page {filters.page} of {pages}</span><button className="button secondary small" disabled={filters.page >= pages} onClick={() => syncParams({ ...filters, page: filters.page + 1 })}>Next</button></div>
    {activeMeta ? <div className="card-section"><h3>Metadata</h3><pre>{JSON.stringify(activeMeta, null, 2)}</pre><button className="button secondary small" onClick={() => setActiveMeta(null)}>Close</button></div> : null}
  </div></div>
}
