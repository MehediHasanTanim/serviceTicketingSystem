import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useRiskRegistry } from '../hooks/useRiskCompliance'
import type { RiskFilters } from '../types/riskCompliance.types'

const baseFilters: RiskFilters = { q: '', risk_level: '', status: '', category: '', property: '', department: '', owner: '', due_from: '', due_to: '', page: 1, page_size: 10 }

export function RiskRegistryPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const [filters, setFilters] = useState<RiskFilters>(baseFilters)
  const { data, loading, error, reload } = useRiskRegistry(auth?.accessToken, auth?.user?.org_id, filters)
  const rows = data?.results || []
  const pages = Math.max(1, Math.ceil((data?.count || 0) / filters.page_size))

  const isOverdue = (dueAt: string | null, status: string) => Boolean(dueAt && new Date(dueAt).getTime() < Date.now() && !['CLOSED', 'VOID'].includes(status))

  return <div className="page full"><div className="glass panel"><div className="section-head"><h2>Risk Registry</h2><button className="button" onClick={() => navigate('/risk-compliance/risks/new')}>New Risk</button></div>
    <div className="grid-form three"><input className="input" placeholder="Search by code/title/category" value={filters.q} onChange={(e) => setFilters((p) => ({ ...p, q: e.target.value, page: 1 }))} /><select className="input" value={filters.risk_level} onChange={(e) => setFilters((p) => ({ ...p, risk_level: e.target.value, page: 1 }))}><option value="">Risk Level</option><option value="LOW">LOW</option><option value="MEDIUM">MEDIUM</option><option value="HIGH">HIGH</option><option value="CRITICAL">CRITICAL</option></select><select className="input" value={filters.status} onChange={(e) => setFilters((p) => ({ ...p, status: e.target.value, page: 1 }))}><option value="">Status</option><option value="OPEN">OPEN</option><option value="MITIGATING">MITIGATING</option><option value="MONITORING">MONITORING</option><option value="ACCEPTED">ACCEPTED</option><option value="CLOSED">CLOSED</option></select></div>
    {loading ? <p>Loading risks...</p> : null}
    {error ? <div><p className="error-text">{error}</p><button className="button secondary small" onClick={reload}>Retry</button></div> : null}
    {!loading && !error && rows.length === 0 ? <p className="hint">No risks found.</p> : null}
    {rows.length > 0 ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Risk Code</th><th>Title</th><th>Category</th><th>Property</th><th>Department</th><th>Owner</th><th>Likelihood</th><th>Impact</th><th>Inherent Score</th><th>Residual Score</th><th>Risk Level</th><th>Status</th><th>Due At</th><th>Actions</th></tr></thead><tbody>{rows.map((row) => <tr key={row.id}><td>{row.risk_code}</td><td>{row.title}</td><td>{row.category || '-'}</td><td>{row.property_id || '-'}</td><td>{row.department_id || '-'}</td><td>{row.owner_id || '-'}</td><td>{row.likelihood}</td><td>{row.impact}</td><td>{row.inherent_score}</td><td>{row.residual_score}</td><td><span className={`badge ${row.risk_level === 'CRITICAL' ? 'critical' : row.risk_level === 'HIGH' ? 'warning' : 'neutral'}`}>{row.risk_level}</span></td><td>{row.status}</td><td>{row.due_at ? new Date(row.due_at).toLocaleString() : '-'} {isOverdue(row.due_at, row.status) ? <span className="badge critical">Overdue</span> : null}</td><td><button className="button secondary small" onClick={() => navigate(`/risk-compliance/risks/${row.id}`)}>Open</button></td></tr>)}</tbody></table></div> : null}
    <div className="pagination-row"><button className="button secondary small" disabled={filters.page <= 1} onClick={() => setFilters((p) => ({ ...p, page: p.page - 1 }))}>Prev</button><span>Page {filters.page} of {pages}</span><button className="button secondary small" disabled={filters.page >= pages} onClick={() => setFilters((p) => ({ ...p, page: p.page + 1 }))}>Next</button></div>
  </div></div>
}
