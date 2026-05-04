import { useEffect, useMemo, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { useAuth } from '../auth/authContext'
import {
  addAttachment,
  addRemark,
  assignServiceOrder,
  deleteAttachment,
  fetchAttachments,
  fetchServiceOrderAuditLogs,
  fetchRemarks,
  fetchServiceOrder,
  transitionServiceOrder,
  updateCosts,
  updateServiceOrder,
} from './api'
import { AssignmentModal } from './components/AssignmentModal'
import { CostCard } from './components/CostCard'
import { OrderForm } from './components/OrderForm'
import { StatusTransitionControls } from './components/StatusTransitionControls'
import { TimelineView } from './components/TimelineView'
import type { ServiceOrder, ServiceOrderAttachment, ServiceOrderRemark, TimelineItem } from './types'
import { formatCurrency } from './utils'

export function ServiceOrderDetailPage() {
  const { auth } = useAuth()
  const params = useParams()
  const [query] = useSearchParams()
  const id = Number(params.id)
  const [activeTab, setActiveTab] = useState<'overview' | 'timeline' | 'attachments' | 'remarks' | 'costs'>('overview')
  const [order, setOrder] = useState<ServiceOrder | null>(null)
  const [remarks, setRemarks] = useState<ServiceOrderRemark[]>([])
  const [attachments, setAttachments] = useState<ServiceOrderAttachment[]>([])
  const [timeline, setTimeline] = useState<TimelineItem[]>([])
  const [auditEvents, setAuditEvents] = useState<Array<{ id: number; actor_user_id: number | null; action: string; created_at: string }>>([])
  const [loading, setLoading] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [showAssign, setShowAssign] = useState(false)
  const [showEdit, setShowEdit] = useState(false)
  const [remarkText, setRemarkText] = useState('')
  const [remarkInternal, setRemarkInternal] = useState(true)
  const [notice, setNotice] = useState('')
  const [uploadProgress, setUploadProgress] = useState(0)

  const load = async () => {
    if (!auth?.accessToken || !auth.user?.org_id || !id) return
    setLoading(true)
    setError('')
    try {
      const [orderData, remarkData, attachmentData, auditData] = await Promise.all([
        fetchServiceOrder(auth.accessToken, auth.user.org_id, id),
        fetchRemarks(auth.accessToken, auth.user.org_id, id),
        fetchAttachments(auth.accessToken, auth.user.org_id, id),
        fetchServiceOrderAuditLogs(auth.accessToken, auth.user.org_id, id).catch(() => ({ count: 0, results: [] })),
      ])
      setOrder(orderData)
      setRemarks(remarkData.results)
      setAttachments(attachmentData.results)
      setAuditEvents(auditData.results)
    } catch (err: any) {
      setError(err.message || 'Failed to load order.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [auth?.accessToken, auth?.user?.org_id, id])
  useEffect(() => {
    if (query.get('edit') === '1') setShowEdit(true)
  }, [query])

  useEffect(() => {
    if (!order) return
    const items: TimelineItem[] = [
      { id: `created-${order.id}`, kind: 'created', actor: `User #${order.created_by}`, at: order.created_at, summary: 'Order created' },
      { id: `updated-${order.id}`, kind: 'updated', actor: 'System', at: order.updated_at, summary: `Status: ${order.status}` },
      ...(order.completed_at ? [{ id: `completed-${order.id}`, kind: 'completed', actor: 'System', at: order.completed_at, summary: 'Order completed' }] : []),
      ...remarks.map((r) => ({ id: `remark-${r.id}`, kind: 'remark', actor: `User #${r.author}`, at: r.created_at, summary: 'Remark added', note: r.text })),
      ...attachments.map((a) => ({ id: `attachment-${a.id}`, kind: 'attachment', actor: `User #${a.uploaded_by}`, at: a.uploaded_at, summary: 'Attachment uploaded', note: a.file_name })),
      ...auditEvents.map((event) => ({
        id: `audit-${event.id}`,
        kind: 'audit',
        actor: event.actor_user_id ? `User #${event.actor_user_id}` : 'System',
        at: event.created_at,
        summary: event.action.split('_').join(' '),
      })),
    ]
    setTimeline(items)
  }, [order, remarks, attachments, auditEvents])

  const apply = (updated: ServiceOrder) => setOrder(updated)

  const runAction = async (action: 'assign' | 'start' | 'hold' | 'complete' | 'defer' | 'void' | 'reassign', reason?: string) => {
    if (!auth?.accessToken || !auth.user?.org_id || !order) return
    if (action === 'assign' || action === 'reassign') {
      setShowAssign(true)
      return
    }
    setBusy(true)
    try {
      const mapped = action === 'hold' ? 'hold' : action
      const updated = await transitionServiceOrder(auth.accessToken, order.id, mapped as any, { org_id: auth.user.org_id, note: reason || '' })
      apply(updated)
      setNotice(`Action "${action}" applied successfully.`)
      await load()
    } finally {
      setBusy(false)
    }
  }

  const submitAssign = async (assigneeId: number, reason?: string) => {
    if (!auth?.accessToken || !auth.user?.org_id || !order) return
    setBusy(true)
    try {
      const updated = await assignServiceOrder(auth.accessToken, order.id, {
        org_id: auth.user.org_id,
        assignee_id: assigneeId,
        reason: reason || '',
      }, order.status === 'DEFERRED' || Boolean(order.assigned_to))
      apply(updated)
      setShowAssign(false)
      setNotice('Assignment updated successfully.')
      await load()
    } finally {
      setBusy(false)
    }
  }

  const saveRemark = async () => {
    if (!auth?.accessToken || !auth.user?.org_id || !order || !remarkText.trim()) return
    setBusy(true)
    try {
      const remark = await addRemark(auth.accessToken, order.id, { org_id: auth.user.org_id, text: remarkText.trim(), is_internal: remarkInternal })
      setRemarks((prev) => [remark, ...prev])
      setRemarkText('')
      setNotice('Remark added.')
    } finally {
      setBusy(false)
    }
  }

  const onUpload = async (file: File | null) => {
    if (!file || !auth?.accessToken || !auth.user?.org_id || !order) return
    const allowed = ['image/', 'application/pdf', 'text/']
    if (!allowed.some((type) => file.type.startsWith(type))) {
      setError('Invalid file type.')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('File too large. Max 10MB.')
      return
    }
    setUploadProgress(5)
    const progressTimer = setInterval(() => {
      setUploadProgress((prev) => (prev >= 85 ? prev : prev + 15))
    }, 150)
    setBusy(true)
    try {
      const uploaded = await addAttachment(auth.accessToken, order.id, {
        org_id: auth.user.org_id,
        file_name: file.name,
        storage_key: `uploads/${Date.now()}-${file.name}`,
      })
      setAttachments((prev) => [uploaded, ...prev])
      setUploadProgress(100)
      setNotice('Attachment uploaded.')
      setTimeout(() => setUploadProgress(0), 300)
    } finally {
      clearInterval(progressTimer)
      setBusy(false)
    }
  }

  const removeAttachment = async (attachmentId: number) => {
    if (!auth?.accessToken || !auth.user?.org_id || !order) return
    setBusy(true)
    try {
      await deleteAttachment(auth.accessToken, order.id, attachmentId, auth.user.org_id)
      setAttachments((prev) => prev.filter((item) => item.id !== attachmentId))
      setNotice('Attachment removed.')
    } finally {
      setBusy(false)
    }
  }

  const saveCosts = async (values: { parts_cost: string; labor_cost: string; compensation_cost: string }) => {
    if (!auth?.accessToken || !auth.user?.org_id || !order) return
    setBusy(true)
    try {
      const updated = await updateCosts(auth.accessToken, order.id, { org_id: auth.user.org_id, ...values })
      apply(updated)
      setNotice('Costs saved.')
      await load()
    } finally {
      setBusy(false)
    }
  }

  const onEdit = async (payload: Record<string, unknown>) => {
    if (!auth?.accessToken || !order) return
    setBusy(true)
    try {
      const updated = await updateServiceOrder(auth.accessToken, order.id, payload)
      apply(updated)
      setShowEdit(false)
      setNotice('Order updated.')
      await load()
    } finally {
      setBusy(false)
    }
  }

  const users = useMemo(() => {
    if (!order) return []
    return [
      { id: order.created_by, label: `User #${order.created_by}` },
      ...(order.assigned_to ? [{ id: order.assigned_to, label: `User #${order.assigned_to}` }] : []),
    ]
  }, [order])

  if (loading) return <div className="page full"><div className="glass panel"><p>Loading order...</p></div></div>
  if (error) return <div className="page full"><div className="glass panel"><p className="error-text">{error}</p><button className="button secondary small" onClick={load}>Retry</button></div></div>
  if (!order) return <div className="page full"><div className="glass panel"><p>Order not found.</p></div></div>

  return (
    <div className="page full">
      <div className="glass panel">
        <div className="section-head">
          <div>
            <h2>{order.ticket_number} • {order.title}</h2>
            <p className="hint">Created {new Date(order.created_at).toLocaleString()} • Assigned to {order.assigned_to ? `#${order.assigned_to}` : 'Unassigned'}</p>
            <div className="badge-row"><span className="badge neutral">{order.status}</span><span className={`badge ${order.priority.toLowerCase()}`}>{order.priority}</span><span className="badge neutral">{order.type}</span></div>
          </div>
          <button className="button secondary small" onClick={() => setShowEdit((v) => !v)}>{showEdit ? 'Close Edit' : 'Edit'}</button>
        </div>
        {notice ? <p className="success-text">{notice}</p> : null}

        <StatusTransitionControls status={order.status} onAction={runAction} busy={busy} />
        {showAssign ? <AssignmentModal open={showAssign} users={users} currentAssigneeId={order.assigned_to} reassign={Boolean(order.assigned_to)} onClose={() => setShowAssign(false)} onSubmit={submitAssign} busy={busy} /> : null}
        {showEdit ? <OrderForm orgId={order.org_id} mode="edit" initial={order} users={users} onSubmit={onEdit} saving={busy} /> : null}

        <div className="tabs-row">
          <button className={`tab ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>Overview</button>
          <button className={`tab ${activeTab === 'timeline' ? 'active' : ''}`} onClick={() => setActiveTab('timeline')}>Timeline</button>
          <button className={`tab ${activeTab === 'attachments' ? 'active' : ''}`} onClick={() => setActiveTab('attachments')}>Attachments</button>
          <button className={`tab ${activeTab === 'remarks' ? 'active' : ''}`} onClick={() => setActiveTab('remarks')}>Remarks</button>
          <button className={`tab ${activeTab === 'costs' ? 'active' : ''}`} onClick={() => setActiveTab('costs')}>Costs</button>
        </div>

        {activeTab === 'overview' ? (
          <div className="card-section">
            <p>{order.description || 'No description.'}</p>
            <div className="grid-form three">
              <div><strong>Customer:</strong> #{order.customer_id}</div>
              <div><strong>Asset:</strong> {order.asset_id ? `#${order.asset_id}` : 'N/A'}</div>
              <div><strong>Total cost:</strong> {formatCurrency(order.total_cost)}</div>
              <div><strong>Due date:</strong> {order.due_date || '-'}</div>
              <div><strong>Scheduled at:</strong> {order.scheduled_at ? new Date(order.scheduled_at).toLocaleString() : '-'}</div>
              <div><strong>Completed at:</strong> {order.completed_at ? new Date(order.completed_at).toLocaleString() : '-'}</div>
            </div>
          </div>
        ) : null}

        {activeTab === 'timeline' ? <TimelineView entries={timeline} /> : null}

        {activeTab === 'attachments' ? (
          <div className="card-section">
            <label className="field" htmlFor="attachment-upload">Upload file
              <input id="attachment-upload" className="input" type="file" onChange={(e) => onUpload(e.target.files?.[0] || null)} />
            </label>
            {uploadProgress > 0 ? <p className="hint">Uploading... {uploadProgress}%</p> : null}
            {attachments.length === 0 ? <p className="hint">No attachments yet.</p> : (
              <ul className="simple-list">
                {attachments.map((a) => (
                  <li key={a.id}>
                    <a href={a.storage_key} target="_blank" rel="noreferrer">{a.file_name}</a>{' '}
                    <button className="button secondary small" onClick={() => removeAttachment(a.id)} disabled={busy}>Delete</button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : null}

        {activeTab === 'remarks' ? (
          <div className="card-section">
            <label className="field" htmlFor="remark-text">Add remark
              <textarea id="remark-text" className="input" rows={4} value={remarkText} onChange={(e) => setRemarkText(e.target.value)} />
            </label>
            <label className="field inline"><input type="checkbox" checked={remarkInternal} onChange={(e) => setRemarkInternal(e.target.checked)} /> Internal remark</label>
            <button className="button small" onClick={saveRemark} disabled={busy}>Save Remark</button>
            {remarks.length === 0 ? <p className="hint">No remarks yet.</p> : (
              <ul className="simple-list">{remarks.map((r) => <li key={r.id}><strong>User #{r.author}</strong> • {new Date(r.created_at).toLocaleString()}<br />{r.text}</li>)}</ul>
            )}
          </div>
        ) : null}

        {activeTab === 'costs' ? (
          <CostCard
            partsCost={order.parts_cost}
            laborCost={order.labor_cost}
            compensationCost={order.compensation_cost}
            onSave={saveCosts}
            busy={busy}
          />
        ) : null}
      </div>
    </div>
  )
}
