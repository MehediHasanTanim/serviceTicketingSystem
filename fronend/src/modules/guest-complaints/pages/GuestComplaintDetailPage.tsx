import { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { LifecycleActions } from '../components/LifecycleActions'
import { isOverdue } from '../components/utils'
import {
  useAssignComplaint,
  useComplaintAuditLog,
  useComplaintFollowUps,
  useComplaintLifecycleAction,
  useConfirmResolution,
  useCreateFollowUp,
  useEscalateComplaint,
  useGuestComplaintDetail,
} from '../hooks/useGuestComplaints'

export function GuestComplaintDetailPage() {
  const { auth } = useAuth()
  const id = Number(useParams().id)
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const [assignTo, setAssignTo] = useState('')
  const [followUp, setFollowUp] = useState({ follow_up_type: '', scheduled_at: '', assigned_to: '', notes: '' })
  const [resolution, setResolution] = useState({ satisfaction_score: '', satisfaction_comment: '', confirmation_channel: '' })
  const { data: complaint, loading, error, reload } = useGuestComplaintDetail(auth?.accessToken, auth?.user?.org_id, id)
  const { data: followUps, reload: reloadFollowUps } = useComplaintFollowUps(auth?.accessToken, auth?.user?.org_id, id)
  const { data: audit } = useComplaintAuditLog(auth?.accessToken, auth?.user?.org_id, { target_id: String(id) })
  const act = useComplaintLifecycleAction()
  const assign = useAssignComplaint()
  const escalate = useEscalateComplaint()
  const createFollowUp = useCreateFollowUp()
  const confirmResolution = useConfirmResolution()

  const runAction = async (action: 'assign' | 'start' | 'escalate' | 'resolve' | 'confirm' | 'reopen' | 'void', reason?: string) => {
    if (!auth?.accessToken || !auth.user?.org_id || !complaint) return
    setBusy(true)
    try {
      if (action === 'assign') {
        if (!assignTo) throw new Error('Assignee is required')
        await assign(auth.accessToken, complaint.id, { org_id: auth.user.org_id, assignee_id: Number(assignTo), reason: reason || '' })
      } else if (action === 'escalate') {
        await escalate(auth.accessToken, complaint.id, { org_id: auth.user.org_id, reason: reason || '', escalation_level: 1 })
      } else if (action === 'start') {
        await act(auth.accessToken, complaint.id, 'start', { org_id: auth.user.org_id })
      } else if (action === 'resolve') {
        await act(auth.accessToken, complaint.id, 'resolve', { org_id: auth.user.org_id })
      } else if (action === 'reopen') {
        await act(auth.accessToken, complaint.id, 'reopen', { org_id: auth.user.org_id, reason: reason || '' })
      } else if (action === 'void') {
        await act(auth.accessToken, complaint.id, 'void', { org_id: auth.user.org_id, reason: reason || '' })
      }
      setNotice(`Action ${action} completed`)
      await reload()
    } catch (err: any) {
      setNotice(err.message || 'Action failed')
    } finally {
      setBusy(false)
    }
  }

  const canConfirmResolution = complaint?.status === 'RESOLVED'
  const lowSatisfaction = Number(resolution.satisfaction_score || '0') <= 2 && resolution.satisfaction_score !== ''

  const createFollowUpNow = async () => {
    if (!auth?.accessToken || !auth.user?.org_id || !complaint) return
    setBusy(true)
    try {
      await createFollowUp(auth.accessToken, complaint.id, { org_id: auth.user.org_id, follow_up_type: followUp.follow_up_type, scheduled_at: new Date(followUp.scheduled_at).toISOString(), assigned_to: followUp.assigned_to ? Number(followUp.assigned_to) : null, notes: followUp.notes })
      setNotice('Follow-up created')
      await reloadFollowUps()
    } finally { setBusy(false) }
  }

  const confirmNow = async () => {
    if (!auth?.accessToken || !auth.user?.org_id || !complaint) return
    if (!canConfirmResolution) return
    setBusy(true)
    try {
      await confirmResolution(auth.accessToken, complaint.id, { org_id: auth.user.org_id, satisfaction_score: resolution.satisfaction_score, satisfaction_comment: resolution.satisfaction_comment, confirmation_channel: resolution.confirmation_channel })
      setNotice('Resolution confirmed')
      await reload()
    } finally { setBusy(false) }
  }

  const timeline = useMemo(() => [{ title: 'Created', at: complaint?.created_at }, { title: 'Updated', at: complaint?.updated_at }, { title: 'Resolved', at: complaint?.resolved_at }, { title: 'Confirmed', at: complaint?.confirmed_at }].filter((x) => x.at), [complaint])

  if (loading) return <div className="page full"><div className="glass panel"><p>Loading complaint...</p></div></div>
  if (error || !complaint) return <div className="page full"><div className="glass panel"><p className="error-text">{error || 'Complaint not found'}</p></div></div>

  return <div className="page full"><div className="glass panel">
    <div className="section-head"><div><h2>{complaint.complaint_number} • {complaint.title}</h2><p className="hint">Guest: {complaint.guest_name} • Room: {complaint.room_id || '-'} • Assigned: {complaint.assigned_to || '-'} • Due: {complaint.due_at ? new Date(complaint.due_at).toLocaleString() : '-'} {isOverdue(complaint.due_at, complaint.status) ? '(Overdue)' : ''}</p><div className="badge-row"><span className="badge neutral">{complaint.status}</span><span className={`badge ${complaint.severity.toLowerCase()}`}>{complaint.severity}</span><span className="badge neutral">{complaint.category}</span></div></div></div>
    {notice ? <p className="hint">{notice}</p> : null}
    <label className="field">Assign To<input className="input" value={assignTo} onChange={(e) => setAssignTo(e.target.value)} placeholder="User ID" /></label>
    <LifecycleActions status={complaint.status} busy={busy} onAction={runAction} />

    <div className="grid-form two">
      <div className="card-section"><h3>Lifecycle / Activity Timeline</h3>{timeline.map((item) => <p key={item.title}><strong>{item.title}:</strong> {item.at ? new Date(item.at).toLocaleString() : '-'}</p>)}</div>
      <div className="card-section"><h3>Follow-ups</h3>{(followUps?.results || []).map((x) => <p key={x.id}><span className="badge neutral">{x.status}</span> {x.follow_up_type} at {new Date(x.scheduled_at).toLocaleString()}</p>)}<label className="field">Type<input className="input" value={followUp.follow_up_type} onChange={(e) => setFollowUp((p) => ({ ...p, follow_up_type: e.target.value }))} /></label><label className="field">Scheduled At<input className="input" type="datetime-local" value={followUp.scheduled_at} onChange={(e) => setFollowUp((p) => ({ ...p, scheduled_at: e.target.value }))} /></label><label className="field">Assigned To<input className="input" value={followUp.assigned_to} onChange={(e) => setFollowUp((p) => ({ ...p, assigned_to: e.target.value }))} /></label><label className="field">Notes<textarea className="input" value={followUp.notes} onChange={(e) => setFollowUp((p) => ({ ...p, notes: e.target.value }))} /></label><button className="button small" disabled={busy || !followUp.follow_up_type || !followUp.scheduled_at} onClick={createFollowUpNow}>Create Follow-up</button></div>
    </div>

    <div className="card-section"><h3>Resolution Confirmation</h3>
      {!canConfirmResolution ? <p className="hint">Available only after RESOLVED.</p> : <>
        <label className="field">Satisfaction Score<input className="input" value={resolution.satisfaction_score} onChange={(e) => setResolution((p) => ({ ...p, satisfaction_score: e.target.value }))} /></label>
        <label className="field">Comment<textarea className="input" value={resolution.satisfaction_comment} onChange={(e) => setResolution((p) => ({ ...p, satisfaction_comment: e.target.value }))} /></label>
        <label className="field">Confirmation Channel<input className="input" value={resolution.confirmation_channel} onChange={(e) => setResolution((p) => ({ ...p, confirmation_channel: e.target.value }))} /></label>
        {lowSatisfaction ? <p className="error-text">Low satisfaction may trigger reopen/escalation.</p> : null}
        <button className="button" disabled={busy || !resolution.satisfaction_score} onClick={confirmNow}>Confirm Resolution</button>
      </>}
    </div>

    <div className="card-section"><h3>Audit History</h3>{(audit?.results || []).length === 0 ? <p className="hint">No audit events.</p> : (audit?.results || []).slice(0, 20).map((x) => <p key={x.id}>{new Date(x.created_at).toLocaleString()} • {x.action}</p>)}</div>
  </div></div>
}
