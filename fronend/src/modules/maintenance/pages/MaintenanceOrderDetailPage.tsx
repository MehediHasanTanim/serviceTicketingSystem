import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { assignMaintenanceOrder, createMaintenanceLogbookEntry, recalculateMaintenanceCosts, transitionMaintenanceOrder } from '../api/maintenance.api'
import { addMaintenanceAttachment, fetchMaintenanceAttachments } from '../api/maintenance.api'
import { useMaintenanceLogbook, useMaintenanceOrderDetail } from '../hooks/useMaintenance'
import { getAllowedActions, sumMoney } from '../components/utils'

export function MaintenanceOrderDetailPage() {
  const { id } = useParams()
  const taskId = Number(id)
  const { auth } = useAuth()
  const detail = useMaintenanceOrderDetail(auth?.accessToken, auth?.user?.org_id, taskId)
  const logbook = useMaintenanceLogbook(auth?.accessToken, auth?.user?.org_id, taskId)
  const [busy, setBusy] = useState(false)
  const [entryType, setEntryType] = useState('NOTE')
  const [entryText, setEntryText] = useState('')
  const [attachments, setAttachments] = useState<Array<{ id: number; file_name: string; storage_key: string; uploaded_at: string }>>([])

  const order = detail.data
  const loadAttachments = async () => {
    if (!auth?.accessToken || !auth.user?.org_id) return
    const rows = await fetchMaintenanceAttachments(auth.accessToken, auth.user.org_id, taskId)
    setAttachments(rows.results)
  }
  useEffect(() => {
    loadAttachments().catch(() => undefined)
  }, [auth?.accessToken, auth?.user?.org_id, taskId])
  if (detail.loading) return <div className="page full"><div className="glass panel"><p>Loading task...</p></div></div>
  if (detail.error || !order) return <div className="page full"><div className="glass panel"><p className="error-text">{detail.error || 'Task not found'}</p></div></div>

  const runAction = async (action: string) => {
    if (!auth?.accessToken || !auth.user?.org_id) return
    if (['complete', 'cancel', 'void'].includes(action) && !window.confirm(`Confirm ${action}?`)) return
    setBusy(true)
    try {
      if (action === 'assign') {
        const next = prompt('Assign technician user ID')
        if (next) {
          await assignMaintenanceOrder(auth.accessToken, order.id, { org_id: auth.user.org_id, assignee_id: Number(next) })
        }
      } else {
        await transitionMaintenanceOrder(auth.accessToken, order.id, action as 'start' | 'hold' | 'complete' | 'cancel' | 'void', { org_id: auth.user.org_id })
      }
      await Promise.all([detail.reload(), logbook.reload()])
    } finally {
      setBusy(false)
    }
  }

  const addEntry = async () => {
    if (!auth?.accessToken || !auth.user?.org_id || !entryText.trim()) return
    setBusy(true)
    try {
      await createMaintenanceLogbookEntry(auth.accessToken, order.id, { org_id: auth.user.org_id, entry_type: entryType, description: entryText.trim() })
      await recalculateMaintenanceCosts(auth.accessToken, order.id, { org_id: auth.user.org_id })
      setEntryText('')
      await Promise.all([detail.reload(), logbook.reload()])
    } finally {
      setBusy(false)
    }
  }

  const entries = (logbook.data?.results || []).slice().sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
  const partsTotal = sumMoney(entries.flatMap((entry) => entry.parts.map((part) => part.total_cost)))
  const laborTotal = sumMoney(entries.flatMap((entry) => entry.labor.map((l) => l.total_labor_cost)))

  return (
    <div className="page full"><div className="glass panel">
      <div className="section-head"><div><h2>{order.task_number} • {order.title}</h2><div className="badge-row"><span className="badge neutral">{order.task_type}</span><span className="badge neutral">{order.status}</span><span className={`badge ${order.priority.toLowerCase()}`}>{order.priority}</span></div></div></div>
      <div className="action-row">{getAllowedActions(order.status).map((action) => <button key={action} className="button secondary small" disabled={busy} onClick={() => runAction(action)}>{action.toUpperCase()}</button>)}</div>
      <div className="grid-form three">
        <div><strong>Asset:</strong> {order.asset_id || '-'}</div><div><strong>Room:</strong> {order.room_id || '-'}</div><div><strong>Assigned:</strong> {order.assigned_to || '-'}</div>
        <div><strong>Due:</strong> {order.due_at ? new Date(order.due_at).toLocaleString() : '-'}</div><div><strong>Parts:</strong> {partsTotal}</div><div><strong>Labor:</strong> {laborTotal}</div>
      </div>
      <div className="card-section">
        <h3>Logbook</h3>
        <div className="grid-form two">
          <select className="input" value={entryType} onChange={(e) => setEntryType(e.target.value)}><option value="DIAGNOSIS">DIAGNOSIS</option><option value="WORK_PERFORMED">WORK_PERFORMED</option><option value="PART_USED">PART_USED</option><option value="LABOR">LABOR</option><option value="NOTE">NOTE</option><option value="COMPLETION_SUMMARY">COMPLETION_SUMMARY</option></select>
          <button className="button" onClick={addEntry} disabled={busy}>Add Entry</button>
        </div>
        <textarea className="input" rows={3} value={entryText} onChange={(e) => setEntryText(e.target.value)} />
        {entries.length === 0 ? <p className="hint">No entries.</p> : <ul className="simple-list">{entries.map((entry) => <li key={entry.id}><strong>{entry.entry_type}</strong> • {new Date(entry.created_at).toLocaleString()}<br />{entry.description}</li>)}</ul>}
      </div>
      <div className="card-section">
        <h3>Attachments</h3>
        <input className="input" type="file" onChange={async (e) => {
          const file = e.target.files?.[0]
          if (!file || !auth?.accessToken || !auth.user?.org_id) return
          await addMaintenanceAttachment(auth.accessToken, order.id, { org_id: auth.user.org_id, file_name: file.name, storage_key: `maintenance/${Date.now()}-${file.name}` })
          await loadAttachments()
        }} />
        {attachments.length === 0 ? <p className="hint">No attachments.</p> : <ul className="simple-list">{attachments.map((a) => <li key={a.id}><a href={a.storage_key} target="_blank" rel="noreferrer">{a.file_name}</a> • {new Date(a.uploaded_at).toLocaleString()}</li>)}</ul>}
      </div>
    </div></div>
  )
}
