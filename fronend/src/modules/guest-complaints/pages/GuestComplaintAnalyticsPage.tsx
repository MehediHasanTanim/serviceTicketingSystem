import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useGuestComplaintAnalytics } from '../hooks/useGuestComplaints'

function Bar({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0
  return <div><div className="hint">{label} ({value})</div><div style={{ background: '#eef1f8', borderRadius: 6, height: 10 }}><div style={{ width: `${pct}%`, background: '#4b55ff', height: 10, borderRadius: 6 }} /></div></div>
}

export function GuestComplaintAnalyticsPage() {
  const { auth } = useAuth()
  const [params, setParams] = useSearchParams()
  const [filters, setFilters] = useState({ group_by: params.get('group_by') || 'day', date_from: params.get('date_from') || '', date_to: params.get('date_to') || '', property: params.get('property') || '', department: params.get('department') || '', category: params.get('category') || '', severity: params.get('severity') || '', source: params.get('source') || '' })
  const { data, loading, error, reload } = useGuestComplaintAnalytics(auth?.accessToken, auth?.user?.org_id, filters)

  useEffect(() => {
    const p = new URLSearchParams()
    Object.entries(filters).forEach(([k, v]) => { if (v) p.set(k, v) })
    setParams(p, { replace: true })
  }, [filters, setParams])

  const s = data?.summary
  const maxCat = Math.max(1, ...(s?.complaints_by_category || []).map((x) => x.count))
  const maxSev = Math.max(1, ...(s?.complaints_by_severity || []).map((x) => x.count))

  return <div className="page full"><div className="glass panel"><div className="section-head"><h2>Guest Experience Analytics</h2><button className="button secondary small" onClick={reload}>Retry</button></div>
    <div className="grid-form filters-grid"><select className="input" value={filters.group_by} onChange={(e) => setFilters((p) => ({ ...p, group_by: e.target.value }))}><option value="day">Day</option><option value="week">Week</option><option value="month">Month</option></select><input className="input" type="date" value={filters.date_from} onChange={(e) => setFilters((p) => ({ ...p, date_from: e.target.value }))} /><input className="input" type="date" value={filters.date_to} onChange={(e) => setFilters((p) => ({ ...p, date_to: e.target.value }))} /><input className="input" placeholder="Property" value={filters.property} onChange={(e) => setFilters((p) => ({ ...p, property: e.target.value }))} /><input className="input" placeholder="Department" value={filters.department} onChange={(e) => setFilters((p) => ({ ...p, department: e.target.value }))} /></div>
    {loading ? <p>Loading analytics...</p> : null}
    {error ? <p className="error-text">{error}</p> : null}
    {data ? <>
      <div className="grid-form three">
        <div className="card-section"><strong>Total</strong><p>{s?.total_complaints || 0}</p></div>
        <div className="card-section"><strong>Open</strong><p>{s?.open_complaints || 0}</p></div>
        <div className="card-section"><strong>Resolved</strong><p>{s?.resolved_complaints || 0}</p></div>
        <div className="card-section"><strong>Escalated</strong><p>{s?.escalated_complaints || 0}</p></div>
        <div className="card-section"><strong>Reopened</strong><p>{s?.reopened_complaints || 0}</p></div>
        <div className="card-section"><strong>SLA %</strong><p>{(s?.sla_compliance_percentage || 0).toFixed(2)}%</p></div>
        <div className="card-section"><strong>Avg Resolution Time (h)</strong><p>{(data.resolution.average_resolution_time_hours || 0).toFixed(2)}</p></div>
        <div className="card-section"><strong>Avg Satisfaction</strong><p>{(data.satisfaction.average_satisfaction_score || 0).toFixed(2)}</p></div>
        <div className="card-section"><strong>Low Satisfaction</strong><p>{data.satisfaction.low_satisfaction_count || 0}</p></div>
      </div>
      <div className="grid-form two"><div className="card-section"><h3>By Category</h3>{(s?.complaints_by_category || []).map((x) => <Bar key={x.category} label={x.category} value={x.count} max={maxCat} />)}</div><div className="card-section"><h3>By Severity</h3>{(s?.complaints_by_severity || []).map((x) => <Bar key={x.severity} label={x.severity} value={x.count} max={maxSev} />)}</div></div>
      <div className="card-section"><h3>Trend</h3>{data.trends.results.length === 0 ? <p className="hint">No trend rows.</p> : <div className="table-wrap"><table className="data-table"><thead><tr><th>Period</th><th>Count</th></tr></thead><tbody>{data.trends.results.map((r, idx) => <tr key={idx}><td>{String(r.period)}</td><td>{r.count}</td></tr>)}</tbody></table></div>}</div>
    </> : null}
  </div></div>
}
