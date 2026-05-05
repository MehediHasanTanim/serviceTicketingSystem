import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { activateComplianceRequirement, deactivateComplianceRequirement } from '../api/riskCompliance.api'
import { useComplianceRequirements } from '../hooks/useRiskCompliance'
import type { ComplianceRequirementFilters } from '../types/riskCompliance.types'

const baseFilters: ComplianceRequirementFilters = { q: '', category: '', property: '', department: '', owner: '', priority: '', status: '', page: 1, page_size: 10 }

export function ComplianceRequirementsPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const [busyId, setBusyId] = useState<number | null>(null)
  const [filters, setFilters] = useState<ComplianceRequirementFilters>({ ...baseFilters, q: params.get('q') || '', page: Number(params.get('page') || 1), category: params.get('category') || '', status: params.get('status') || '' })
  const { data, loading, error, reload } = useComplianceRequirements(auth?.accessToken, auth?.user?.org_id, filters)

  const sync = (next: ComplianceRequirementFilters) => {
    const p = new URLSearchParams()
    if (next.q) p.set('q', next.q)
    if (next.category) p.set('category', next.category)
    if (next.status) p.set('status', next.status)
    p.set('page', String(next.page))
    setParams(p, { replace: true })
    setFilters(next)
  }

  const onToggle = async (id: number, active: boolean) => {
    if (!auth?.accessToken || !auth?.user?.org_id) return
    setBusyId(id)
    try {
      const payload = { org_id: auth.user.org_id }
      if (active) await deactivateComplianceRequirement(auth.accessToken, id, payload)
      else await activateComplianceRequirement(auth.accessToken, id, payload)
      await reload()
    } finally {
      setBusyId(null)
    }
  }

  const rows = data?.results || []
  const pages = Math.max(1, Math.ceil((data?.count || 0) / filters.page_size))

  return <div className="page full"><div className="glass panel"><div className="section-head"><h2>Compliance Requirements</h2><button className="button" onClick={() => navigate('/risk-compliance/requirements/new')}>New Requirement</button></div>
    <div className="grid-form filters-grid"><input className="input" placeholder="Search code/title" value={filters.q} onChange={(e) => sync({ ...filters, q: e.target.value, page: 1 })} /><input className="input" placeholder="Category" value={filters.category} onChange={(e) => sync({ ...filters, category: e.target.value, page: 1 })} /><select className="input" value={filters.status} onChange={(e) => sync({ ...filters, status: e.target.value, page: 1 })}><option value="">Status</option><option value="ACTIVE">ACTIVE</option><option value="INACTIVE">INACTIVE</option><option value="ARCHIVED">ARCHIVED</option></select></div>
    {loading ? <p>Loading requirements...</p> : null}
    {error ? <div><p className="error-text">{error}</p><button className="button secondary small" onClick={reload}>Retry</button></div> : null}
    {!loading && !error && rows.length === 0 ? <p className="hint">No requirements found.</p> : null}
    {rows.length > 0 ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Code</th><th>Title</th><th>Category</th><th>Property</th><th>Department</th><th>Owner</th><th>Priority</th><th>Frequency</th><th>Status</th><th>Effective</th><th>Expiry</th><th>Actions</th></tr></thead><tbody>{rows.map((row) => <tr key={row.id} onClick={() => navigate(`/risk-compliance/requirements/${row.id}`)}><td>{row.requirement_code}</td><td>{row.title}</td><td>{row.category || '-'}</td><td>{row.property_id || '-'}</td><td>{row.department_id || '-'}</td><td>{row.owner_id || '-'}</td><td><span className={`badge ${row.priority === 'CRITICAL' ? 'critical' : 'neutral'}`}>{row.priority}</span></td><td>{row.frequency_type}/{row.frequency_interval}</td><td><span className="badge neutral">{row.status}</span></td><td>{row.effective_date || '-'}</td><td>{row.expiry_date || '-'}</td><td><button className="button secondary small" onClick={(e) => { e.stopPropagation(); void onToggle(row.id, row.status === 'ACTIVE') }} disabled={busyId === row.id}>{row.status === 'ACTIVE' ? 'Deactivate' : 'Activate'}</button></td></tr>)}</tbody></table></div> : null}
    <div className="pagination-row"><button className="button secondary small" disabled={filters.page <= 1} onClick={() => sync({ ...filters, page: filters.page - 1 })}>Prev</button><span>Page {filters.page} of {pages}</span><button className="button secondary small" disabled={filters.page >= pages} onClick={() => sync({ ...filters, page: filters.page + 1 })}>Next</button></div>
  </div></div>
}
