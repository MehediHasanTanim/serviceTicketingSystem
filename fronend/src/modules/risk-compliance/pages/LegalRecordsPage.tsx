import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useLegalRecords } from '../hooks/useRiskCompliance'
import type { LegalRecordFilters } from '../types/riskCompliance.types'

const baseFilters: LegalRecordFilters = { q: '', type: '', status: '', property: '', department: '', owner: '', expiry_from: '', expiry_to: '', page: 1, page_size: 10 }

export function LegalRecordsPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const [filters, setFilters] = useState<LegalRecordFilters>({ ...baseFilters, type: params.get('type') || '', status: params.get('status') || '' })
  const { data, loading, error, reload } = useLegalRecords(auth?.accessToken, auth?.user?.org_id, filters)

  const sync = (next: LegalRecordFilters) => {
    const p = new URLSearchParams()
    if (next.type) p.set('type', next.type)
    if (next.status) p.set('status', next.status)
    setParams(p, { replace: true })
    setFilters(next)
  }

  const rows = data?.results || []
  const pages = Math.max(1, Math.ceil((data?.count || 0) / filters.page_size))

  return <div className="page full"><div className="glass panel"><div className="section-head"><h2>Legal / Contract Records</h2><button className="button" onClick={() => navigate('/risk-compliance/legal-records/new')}>New Record</button></div>
    <div className="grid-form three"><input className="input" placeholder="Search code/title/vendor" value={filters.q} onChange={(e) => sync({ ...filters, q: e.target.value, page: 1 })} /><select className="input" value={filters.type} onChange={(e) => sync({ ...filters, type: e.target.value, page: 1 })}><option value="">Type</option><option value="LEGAL">LEGAL</option><option value="CONTRACT">CONTRACT</option><option value="LICENSE">LICENSE</option><option value="PERMIT">PERMIT</option><option value="INSURANCE">INSURANCE</option><option value="AUDIT">AUDIT</option></select><select className="input" value={filters.status} onChange={(e) => sync({ ...filters, status: e.target.value, page: 1 })}><option value="">Status</option><option value="ACTIVE">ACTIVE</option><option value="EXPIRED">EXPIRED</option><option value="RENEWAL_DUE">RENEWAL_DUE</option><option value="ARCHIVED">ARCHIVED</option></select></div>
    {loading ? <p>Loading legal records...</p> : null}
    {error ? <div><p className="error-text">{error}</p><button className="button secondary small" onClick={reload}>Retry</button></div> : null}
    {rows.length > 0 ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Record Code</th><th>Type</th><th>Status</th><th>Expiry Date</th><th>Renewal Due</th><th>Actions</th></tr></thead><tbody>{rows.map((row) => { const expiring = Boolean(row.expiry_date && new Date(row.expiry_date).getTime() - Date.now() < 1000 * 60 * 60 * 24 * 30); return <tr key={row.id}><td>{row.record_code}</td><td>{row.record_type}</td><td>{row.status}</td><td>{row.expiry_date || '-'} {expiring ? <span className="badge warning">Expiring soon</span> : null}</td><td>{row.renewal_due_at ? new Date(row.renewal_due_at).toLocaleString() : '-'}</td><td><button className="button secondary small" onClick={() => navigate(`/risk-compliance/legal-records/${row.id}`)}>Open</button></td></tr> })}</tbody></table></div> : null}
    <div className="pagination-row"><button className="button secondary small" disabled={filters.page <= 1} onClick={() => sync({ ...filters, page: filters.page - 1 })}>Prev</button><span>Page {filters.page} of {pages}</span><button className="button secondary small" disabled={filters.page >= pages} onClick={() => sync({ ...filters, page: filters.page + 1 })}>Next</button></div>
  </div></div>
}
