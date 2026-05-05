import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { usePMCalendar } from '../hooks/useMaintenance'
import type { MaintenanceOrderFilters } from '../types/maintenance.types'

export function PMCalendarPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const [date, setDate] = useState(new Date())
  const [view, setView] = useState<'month' | 'week' | 'day'>('month')
  const [filters, setFilters] = useState<MaintenanceOrderFilters>({ q: '', task_type: 'PREVENTIVE', status: '', priority: '', asset: '', room: '', property: '', department: '', assigned_to: '', date_from: '', date_to: '', page: 1, page_size: 100 })
  const { calendarItems, loading } = usePMCalendar(auth?.accessToken, auth?.user?.org_id, filters)

  const label = useMemo(() => date.toLocaleDateString(undefined, { month: 'long', year: 'numeric' }), [date])
  return <div className="page full"><div className="glass panel"><div className="section-head"><h2>PM Calendar</h2><div><button className="button secondary small" onClick={() => setDate(new Date(date.getFullYear(), date.getMonth() - 1, 1))}>Prev</button><span className="hint"> {label} </span><button className="button secondary small" onClick={() => setDate(new Date(date.getFullYear(), date.getMonth() + 1, 1))}>Next</button></div></div>
    <div className="grid-form three"><select className="input" value={view} onChange={(e) => setView(e.target.value as 'month' | 'week' | 'day')}><option value="month">Month</option><option value="week">Week</option><option value="day">Day/List</option></select><input className="input" placeholder="Property" value={filters.property} onChange={(e) => setFilters((p) => ({ ...p, property: e.target.value }))} /><input className="input" placeholder="Asset" value={filters.asset} onChange={(e) => setFilters((p) => ({ ...p, asset: e.target.value }))} /></div>
    {loading ? <p>Loading calendar...</p> : null}
    {calendarItems.length === 0 && !loading ? <p className="hint">No scheduled PM tasks.</p> : null}
    <ul className="simple-list">{calendarItems.map((item) => <li key={item.id}><button className="button secondary small" onClick={() => navigate(`/maintenance/orders/${item.id}`)}>{new Date(item.at).toLocaleString()} • {item.title} • {item.priority} {item.overdue ? '(Overdue)' : ''}</button></li>)}</ul>
  </div></div>
}
