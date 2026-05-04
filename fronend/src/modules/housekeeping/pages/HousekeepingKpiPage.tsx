import { useState } from 'react'
import { useAuth } from '../../../features/auth/authContext'
import { useHousekeepingKpis } from '../hooks/useHousekeepingKpis'

export function HousekeepingKpiPage() {
  const { auth } = useAuth()
  const [propertyId, setPropertyId] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const { summary, staff, turnaround, loading, error, reload } = useHousekeepingKpis(auth?.accessToken, {
    org_id: auth?.user?.org_id || 0,
    property_id: propertyId || undefined,
    date_from: dateFrom ? `${dateFrom}T00:00:00Z` : undefined,
    date_to: dateTo ? `${dateTo}T23:59:59Z` : undefined,
  })

  return <div className="page full"><div className="glass panel"><div className="section-head"><h2>Housekeeping KPI Dashboard</h2><button className="button secondary small" onClick={reload}>Refresh</button></div>
    <div className="grid-form filters-grid"><input className="input" placeholder="Property ID" value={propertyId} onChange={(e) => setPropertyId(e.target.value)} /><input className="input" type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} /><input className="input" type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} /></div>
    {loading ? <p className="helper">Loading KPI...</p> : null}
    {error ? <p className="error">{error}</p> : null}
    <div className="cards-grid" aria-label="KPI cards"><article className="glass panel"><h3>Total Created</h3><p>{summary.total_tasks_created}</p></article><article className="glass panel"><h3>Total Completed</h3><p>{summary.total_tasks_completed}</p></article><article className="glass panel"><h3>Pending</h3><p>{summary.pending_tasks_count}</p></article><article className="glass panel"><h3>Overdue</h3><p>{summary.overdue_tasks_count}</p></article><article className="glass panel"><h3>Avg Completion</h3><p>{summary.avg_completion_minutes}</p></article><article className="glass panel"><h3>SLA %</h3><p>{summary.sla_compliance_pct}</p></article></div>
    <h3>Staff Performance</h3><div className="table-wrap"><table className="data-table"><thead><tr><th>Staff</th><th>Completed</th><th>Avg Minutes</th></tr></thead><tbody>{staff.map((row) => <tr key={row.staff_id}><td>{row.display_name}</td><td>{row.tasks_completed}</td><td>{row.avg_completion_minutes}</td></tr>)}</tbody></table></div>
    <h3>Room Turnaround</h3><p>Events: {turnaround.events} | Avg Minutes: {turnaround.average_minutes}</p>
  </div></div>
}
