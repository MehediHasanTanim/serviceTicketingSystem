import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useAuditRecords } from '../hooks/useRiskCompliance'

export function AuditRecordsPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const { data, loading, error, reload } = useAuditRecords(auth?.accessToken, auth?.user?.org_id)

  return <div className="page full"><div className="glass panel"><div className="section-head"><h2>Audit Records</h2><button className="button" onClick={() => navigate('/risk-compliance/audit-records/new')}>New Audit Record</button></div>
    {loading ? <p>Loading audit records...</p> : null}
    {error ? <div><p className="error-text">{error}</p><button className="button secondary small" onClick={reload}>Retry</button></div> : null}
    <div className="table-wrap"><table className="data-table"><thead><tr><th>Audit Code</th><th>Result</th><th>Score</th><th>Corrective Actions Required</th><th>Actions</th></tr></thead><tbody>{(data?.results || []).map((row) => <tr key={row.id}><td>{row.audit_code}</td><td>{row.result}</td><td>{row.score ?? '-'}</td><td>{row.corrective_actions_required ? 'Yes' : 'No'}</td><td><button className="button secondary small" onClick={() => navigate(`/risk-compliance/audit-records/${row.id}`)}>Open</button></td></tr>)}</tbody></table></div>
  </div></div>
}
