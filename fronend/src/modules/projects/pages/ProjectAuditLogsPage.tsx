import { useState } from 'react'
import { useAuth } from '../../../features/auth/authContext'
import { AuditLogs } from '../components/AuditLogs'
import { useProjectAuditLogs } from '../hooks/useProjects'
import type { ProjectAuditLogFilters } from '../types/projects.types'

const base: ProjectAuditLogFilters = { q: '', property_id: '', actor_user_id: '', action: '', target_type: '', target_id: '', date_from: '', date_to: '', page: 1, page_size: 10, sort_by: 'created_at', sort_dir: 'desc' }

export function ProjectAuditLogsPage() {
  const { auth } = useAuth()
  const [filters, setFilters] = useState<ProjectAuditLogFilters>(base)
  const { data, loading, error } = useProjectAuditLogs(auth?.accessToken, auth?.user?.org_id, filters)
  const pages = Math.max(1, Math.ceil((data?.count || 0) / filters.page_size))

  return <div className="page full"><div className="glass panel"><h2>Project Audit Logs</h2>
    <div className="grid-form three"><input className="input" placeholder="Action" value={filters.action} onChange={(e) => setFilters((p) => ({ ...p, action: e.target.value, page: 1 }))} /><input className="input" placeholder="Entity Type" value={filters.target_type} onChange={(e) => setFilters((p) => ({ ...p, target_type: e.target.value, page: 1 }))} /><input className="input" placeholder="Actor ID" value={filters.actor_user_id} onChange={(e) => setFilters((p) => ({ ...p, actor_user_id: e.target.value, page: 1 }))} /></div>
    {loading ? <p>Loading logs...</p> : null}
    {error ? <p className="error-text">{error}</p> : null}
    <AuditLogs rows={data?.results || []} />
    <div className="pagination-row"><button className="button secondary small" disabled={filters.page <= 1} onClick={() => setFilters((p) => ({ ...p, page: p.page - 1 }))}>Prev</button><span>Page {filters.page} of {pages}</span><button className="button secondary small" disabled={filters.page >= pages} onClick={() => setFilters((p) => ({ ...p, page: p.page + 1 }))}>Next</button></div>
  </div></div>
}
