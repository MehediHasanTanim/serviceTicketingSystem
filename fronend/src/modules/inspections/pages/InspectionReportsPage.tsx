import { useState } from 'react'
import { useAuth } from '../../../features/auth/authContext'
import { useInspectionReports } from '../hooks/useInspections'

export function InspectionReportsPage() {
  const { auth } = useAuth()
  const [groupBy, setGroupBy] = useState('day')
  const { data, loading, error, reload } = useInspectionReports(auth?.accessToken, auth?.user?.org_id, groupBy)
  const summary = data?.summary

  return <div className="page full"><div className="glass panel"><div className="section-head"><h2>Inspection Reports</h2><button className="button secondary small" onClick={reload}>Retry</button></div>
    <div className="grid-form three"><select className="input" value={groupBy} onChange={(e) => setGroupBy(e.target.value)}><option value="day">Day</option><option value="week">Week</option><option value="month">Month</option></select></div>
    {loading ? <p>Loading report...</p> : null}
    {error ? <p className="error-text">{error}</p> : null}
    <div className="grid-form three">
      <div className="card-section"><strong>Total</strong><p>{summary?.total_inspections || 0}</p></div>
      <div className="card-section"><strong>Completed</strong><p>{summary?.completed_inspections || 0}</p></div>
      <div className="card-section"><strong>Passed</strong><p>{summary?.passed_inspections || 0}</p></div>
      <div className="card-section"><strong>Failed</strong><p>{summary?.failed_inspections || 0}</p></div>
      <div className="card-section"><strong>Average score</strong><p>{(summary?.average_score || 0).toFixed(2)}%</p></div>
      <div className="card-section"><strong>Non-compliance</strong><p>{summary?.non_compliance_count || 0}</p></div>
    </div>
    <div className="card-section"><h3>Score Trend</h3>{(data?.trends || []).length === 0 ? <p className="hint">No trend data.</p> : <div className="table-wrap"><table className="data-table"><thead><tr><th>Period</th><th>Total</th><th>Avg Score</th><th>Pass</th><th>Fail</th></tr></thead><tbody>{(data?.trends || []).map((row) => <tr key={row.period}><td>{row.period}</td><td>{row.total}</td><td>{Number(row.average_score || 0).toFixed(2)}</td><td>{row.pass_count}</td><td>{row.fail_count}</td></tr>)}</tbody></table></div>}</div>
  </div></div>
}
