import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { AssignmentModal } from '../components/AssignmentModal'
import { useAssignFBTask, useFBTaskAction, useFBTasks } from '../hooks/useFoodBeverage'
import type { FBTaskFilters, FBTaskStatus } from '../types/foodBeverage.types'

const base: FBTaskFilters = { property_id: '', outlet_id: '', task_type: '', priority: '', status: '', staff_id: '', date_from: '', date_to: '', q: '', page: 1, page_size: 10 }

function allowed(status: FBTaskStatus) { return { start: ['PENDING','ASSIGNED'].includes(status), complete: status === 'IN_PROGRESS', cancel: ['PENDING','ASSIGNED','IN_PROGRESS'].includes(status), void: status !== 'VOID' && status !== 'COMPLETED' } }

export function FBTasksPage() {
  const { auth } = useAuth(); const navigate = useNavigate(); const [filters, setFilters] = useState(base)
  const [assigning, setAssigning] = useState<number | null>(null); const [saving, setSaving] = useState(false); const [err, setErr] = useState('')
  const [confirm, setConfirm] = useState<{ id: number; action: 'complete'|'cancel'|'void'|'' }>({ id: 0, action: '' })
  const { data, loading, error, reload } = useFBTasks(auth?.accessToken, auth?.user?.org_id, filters)
  const assign = useAssignFBTask(); const act = useFBTaskAction(); const rows = data?.results || []

  const runAction = async (id: number, action: 'start'|'complete'|'cancel'|'void', reason?: string) => {
    if (!auth?.accessToken) return
    setSaving(true); setErr('')
    try { await act(auth.accessToken, id, action, { org_id: auth.user?.org_id, reason }); setConfirm({ id: 0, action: '' }); await reload() } catch (e: any) { setErr(e.message || 'Action failed') } finally { setSaving(false) }
  }

  return <div className="page full"><div className="glass panel"><h2>F&B Tasks</h2>
    <div className="grid-form filters-grid"><input className="input" placeholder="Search task/outlet" value={filters.q} onChange={(e) => setFilters((p) => ({ ...p, q: e.target.value, page: 1 }))} /><input className="input" placeholder="Property ID" value={filters.property_id} onChange={(e) => setFilters((p) => ({ ...p, property_id: e.target.value, page: 1 }))} /><input className="input" placeholder="Outlet ID" value={filters.outlet_id} onChange={(e) => setFilters((p) => ({ ...p, outlet_id: e.target.value, page: 1 }))} /></div>
    {loading ? <p>Loading tasks...</p> : null}{error ? <p className="error-text">{error}</p> : null}{err ? <p className="error-text">{err}</p> : null}
    <div className="table-wrap"><table className="data-table"><thead><tr><th>Task Number</th><th>Outlet</th><th>Title</th><th>Type</th><th>Priority</th><th>Status</th><th>Assigned To</th><th>Due At</th><th>Started At</th><th>Completed At</th><th>Actions</th></tr></thead><tbody>{rows.map((r) => { const a = allowed(r.status); const overdue = !!r.due_at && new Date(r.due_at).getTime() < Date.now() && !['COMPLETED','CANCELLED','VOID'].includes(r.status); return <tr key={r.id}><td>{r.task_number}</td><td>{r.outlet_id || '-'}</td><td>{r.title}</td><td>{r.task_type}</td><td><span className={`badge ${r.priority.toLowerCase()}`}>{r.priority}</span></td><td><span className="badge neutral">{r.status}</span> {overdue ? <span className="badge critical">Overdue</span> : null}</td><td>{r.assigned_to || '-'}</td><td>{r.due_at ? new Date(r.due_at).toLocaleString() : '-'}</td><td>{r.started_at ? new Date(r.started_at).toLocaleString() : '-'}</td><td>{r.completed_at ? new Date(r.completed_at).toLocaleString() : '-'}</td><td><div className="row-actions"><button className="button secondary small" onClick={() => setAssigning(r.id)}>Assign</button>{a.start ? <button className="button secondary small" disabled={saving} onClick={() => void runAction(r.id, 'start')}>Start</button> : null}{a.complete ? <button className="button secondary small" onClick={() => setConfirm({ id: r.id, action: 'complete' })}>Complete</button> : null}{a.cancel ? <button className="button secondary small" onClick={() => setConfirm({ id: r.id, action: 'cancel' })}>Cancel</button> : null}{a.void ? <button className="button secondary small" onClick={() => setConfirm({ id: r.id, action: 'void' })}>Void</button> : null}<button className="button secondary small" onClick={() => navigate(`/food-beverage/tasks/${r.id}`)}>Open</button></div></td></tr> })}</tbody></table></div>
    <AssignmentModal open={!!assigning} currentAssigneeId={rows.find((x) => x.id === assigning)?.assigned_to || null} staff={[{ id: 101, label: 'Staff #101' }, { id: 102, label: 'Staff #102' }, { id: 103, label: 'Staff #103' }]} saving={saving} onClose={() => setAssigning(null)} onSubmit={async (assignee, reason) => {
      if (!auth?.accessToken || !assigning) return
      setSaving(true); setErr('')
      try { await assign(auth.accessToken, assigning, { org_id: auth.user?.org_id, assignee_id: assignee, reason }); setAssigning(null); await reload() } catch (e: any) { setErr(e.message || 'Assignment failed') } finally { setSaving(false) }
    }} />
    {confirm.action ? <div className="modal-backdrop" role="presentation"><div className="modal" role="dialog" aria-modal="true" aria-label="Task action confirmation"><p>Confirm {confirm.action}?</p><label className="field">Reason<input id="action-reason" className="input" /></label><div className="modal-actions"><button className="button secondary small" onClick={() => setConfirm({ id: 0, action: '' })}>Cancel</button><button className="button small" onClick={() => { const el = document.getElementById('action-reason') as HTMLInputElement | null; if (confirm.action) void runAction(confirm.id, confirm.action, el?.value || '') }}>Confirm</button></div></div></div> : null}
  </div></div>
}
