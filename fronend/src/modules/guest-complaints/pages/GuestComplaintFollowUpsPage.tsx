import { useState } from 'react'
import { useAuth } from '../../../features/auth/authContext'
import { useComplaintFollowUps, useCompleteFollowUp } from '../hooks/useGuestComplaints'

export function GuestComplaintFollowUpsPage() {
  const { auth } = useAuth()
  const [complaintId, setComplaintId] = useState('')
  const [notes, setNotes] = useState('')
  const [selected, setSelected] = useState<number | null>(null)
  const [busy, setBusy] = useState(false)
  const followUps = useComplaintFollowUps(auth?.accessToken, auth?.user?.org_id, complaintId ? Number(complaintId) : undefined)
  const completeFollowUp = useCompleteFollowUp()

  const complete = async () => {
    if (!auth?.accessToken || !selected) return
    setBusy(true)
    try { await completeFollowUp(auth.accessToken, selected, { notes }); await followUps.reload() } finally { setBusy(false) }
  }

  return <div className="page full"><div className="glass panel"><h2>Complaint Follow-ups</h2>
    <label className="field">Complaint ID<input className="input" value={complaintId} onChange={(e) => setComplaintId(e.target.value)} /></label>
    <button className="button secondary small" onClick={followUps.reload} disabled={!complaintId}>Load</button>
    {followUps.loading ? <p>Loading...</p> : null}
    {followUps.error ? <p className="error-text">{followUps.error}</p> : null}
    <div className="table-wrap"><table className="data-table"><thead><tr><th>Type</th><th>Scheduled</th><th>Status</th><th>Assigned</th><th>Notes</th><th>Completed</th><th>Action</th></tr></thead><tbody>{(followUps.data?.results || []).map((x) => <tr key={x.id}><td>{x.follow_up_type}</td><td>{new Date(x.scheduled_at).toLocaleString()}</td><td><span className="badge neutral">{x.status}</span></td><td>{x.assigned_to || '-'}</td><td>{x.notes || '-'}</td><td>{x.completed_at ? new Date(x.completed_at).toLocaleString() : '-'}</td><td><button className="button small" disabled={x.status === 'COMPLETED'} onClick={() => setSelected(x.id)}>Select</button></td></tr>)}</tbody></table></div>
    {selected ? <div className="card-section"><h3>Complete Follow-up #{selected}</h3><label className="field">Completion Notes<textarea className="input" value={notes} onChange={(e) => setNotes(e.target.value)} /></label><button className="button" disabled={busy} onClick={complete}>Complete</button></div> : null}
  </div></div>
}
