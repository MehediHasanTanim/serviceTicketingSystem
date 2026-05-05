import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useComplaintAlerts } from '../hooks/useGuestComplaints'

export function GuestComplaintAlertsPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const [severity, setSeverity] = useState('')
  const [status, setStatus] = useState('')
  const [department, setDepartment] = useState('')
  const [assigned_to, setAssignedTo] = useState('')
  const { data, loading, error, reload } = useComplaintAlerts(auth?.accessToken, auth?.user?.org_id, { q: '', status, severity, category: '', source: '', property: '', department, assigned_to, escalated_to: '', date_from: '', date_to: '', page: 1, page_size: 100 })
  const rows = data || []

  return <div className="page full"><div className="glass panel"><div className="section-head"><h2>Complaint Alerts</h2><button className="button secondary small" onClick={reload}>Refresh</button></div>
    <div className="grid-form filters-grid"><select className="input" value={severity} onChange={(e) => setSeverity(e.target.value)}><option value="">All severity</option>{['LOW','MEDIUM','HIGH','CRITICAL'].map((x) => <option key={x} value={x}>{x}</option>)}</select><input className="input" placeholder="Status" value={status} onChange={(e) => setStatus(e.target.value)} /><input className="input" placeholder="Department" value={department} onChange={(e) => setDepartment(e.target.value)} /><input className="input" placeholder="Assigned to" value={assigned_to} onChange={(e) => setAssignedTo(e.target.value)} /></div>
    {loading ? <p>Loading alerts...</p> : null}
    {error ? <p className="error-text">{error}</p> : null}
    {!loading && !error && rows.length === 0 ? <p className="hint">No active alerts.</p> : null}
    {rows.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Complaint #</th><th>Severity</th><th>Status</th><th>Guest/Room</th><th>Assigned</th><th>Reason</th><th>Triggered</th><th>SLA Due</th><th>Actions</th></tr></thead><tbody>{rows.map((row, i) => <tr key={`${row.complaint.id}-${i}`}><td>{row.complaint.complaint_number}</td><td><span className={`badge ${row.complaint.severity.toLowerCase()}`}>{row.complaint.severity}</span></td><td>{row.complaint.status}</td><td>{row.complaint.guest_name} / {row.complaint.room_id || '-'}</td><td>{row.complaint.assigned_to || '-'}</td><td>{row.reason}</td><td>{new Date(row.triggered_at).toLocaleString()}</td><td>{row.complaint.due_at ? new Date(row.complaint.due_at).toLocaleString() : '-'}</td><td><button className="button small" onClick={() => navigate(`/guest-complaints/${row.complaint.id}`)}>Open</button></td></tr>)}</tbody></table></div> : null}
  </div></div>
}
