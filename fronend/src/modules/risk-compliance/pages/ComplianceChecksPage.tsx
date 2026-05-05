import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { ComplianceStatusBadge, OverdueIndicator } from '../components/ComplianceStatusBadge'
import { useComplianceChecks } from '../hooks/useRiskCompliance'
import type { ComplianceCheckFilters } from '../types/riskCompliance.types'

const baseFilters: ComplianceCheckFilters = { requirement_id: '', status: '', property: '', department: '', owner: '', assigned_to: '', priority: '', category: '', page: 1, page_size: 10 }

export function ComplianceChecksPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const [filters, setFilters] = useState<ComplianceCheckFilters>(baseFilters)
  const { data, loading, error, reload } = useComplianceChecks(auth?.accessToken, auth?.user?.org_id, filters)
  const rows = data?.results || []
  const pages = Math.max(1, Math.ceil((data?.count || 0) / filters.page_size))

  return <div className="page full"><div className="glass panel"><h2>Compliance Checks</h2>
    <div className="grid-form three"><input className="input" placeholder="Requirement ID" value={filters.requirement_id} onChange={(e) => setFilters((p) => ({ ...p, requirement_id: e.target.value, page: 1 }))} /><select className="input" value={filters.status} onChange={(e) => setFilters((p) => ({ ...p, status: e.target.value, page: 1 }))}><option value="">Status</option><option value="PENDING">PENDING</option><option value="COMPLIANT">COMPLIANT</option><option value="NON_COMPLIANT">NON_COMPLIANT</option><option value="WAIVED">WAIVED</option><option value="OVERDUE">OVERDUE</option></select></div>
    {loading ? <p>Loading checks...</p> : null}
    {error ? <div><p className="error-text">{error}</p><button className="button secondary small" onClick={reload}>Retry</button></div> : null}
    {!loading && !error && rows.length === 0 ? <p className="hint">No checks found.</p> : null}
    {rows.length > 0 ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Requirement</th><th>Due At</th><th>Status</th><th>Assigned To</th><th>Completed By</th><th>Completed At</th><th>Evidence</th><th>Actions</th></tr></thead><tbody>{rows.map((row) => <tr key={row.id}><td>{row.requirement_id}</td><td>{row.due_at ? new Date(row.due_at).toLocaleString() : '-'}</td><td><ComplianceStatusBadge status={row.status} /> <OverdueIndicator dueAt={row.due_at} status={row.status} /></td><td>{row.assigned_to || '-'}</td><td>{row.completed_by || '-'}</td><td>{row.completed_at ? new Date(row.completed_at).toLocaleString() : '-'}</td><td>{row.evidence_attachment_id ? `#${row.evidence_attachment_id}` : '-'}</td><td><button className="button secondary small" onClick={() => navigate(`/risk-compliance/checks/${row.id}`)}>Open</button></td></tr>)}</tbody></table></div> : null}
    <div className="pagination-row"><button className="button secondary small" disabled={filters.page <= 1} onClick={() => setFilters((p) => ({ ...p, page: p.page - 1 }))}>Prev</button><span>Page {filters.page} of {pages}</span><button className="button secondary small" disabled={filters.page >= pages} onClick={() => setFilters((p) => ({ ...p, page: p.page + 1 }))}>Next</button></div>
  </div></div>
}
