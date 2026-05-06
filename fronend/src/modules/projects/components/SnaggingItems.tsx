import { useState } from 'react'
import type { SnagSeverity, SnaggingItem } from '../types/projects.types'
import { allowedSnagActions, priorityClass } from './utils'

export function SnaggingItems({ items, onOpen, onAction, busy }: { items: SnaggingItem[]; onOpen: (id: number) => void; onAction: (id: number, action: 'assign' | 'start' | 'resolve' | 'verify' | 'reopen' | 'cancel' | 'void', payload: Record<string, unknown>) => Promise<void>; busy?: boolean }) {
  const criticalUnresolved = items.some((x) => x.severity === 'CRITICAL' && !['RESOLVED', 'VERIFIED', 'CANCELLED', 'VOID'].includes(x.status))
  const isOverdue = (x: SnaggingItem) => !!x.due_at && new Date(x.due_at).getTime() < Date.now() && !['RESOLVED', 'VERIFIED', 'CANCELLED', 'VOID'].includes(x.status)

  return <>
    {criticalUnresolved ? <p className="error-text">Critical unresolved snagging items exist.</p> : null}
    <div className="table-wrap"><table className="data-table"><thead><tr><th>Snag Number</th><th>Title</th><th>Category</th><th>Severity</th><th>Status</th><th>Location/Room/Asset</th><th>Assigned To</th><th>Due At</th><th>Resolved At</th><th>Verified At</th><th>Actions</th></tr></thead><tbody>
      {items.map((row) => <tr key={row.id} onClick={() => onOpen(row.id)} className={row.severity === 'CRITICAL' && row.status !== 'VERIFIED' ? 'row-critical' : ''}>
        <td>{row.snag_number}</td><td>{row.title}</td><td>{row.category}</td><td><span className={`badge ${priorityClass(row.severity as SnagSeverity)}`}>{row.severity}</span></td><td><span className="badge neutral">{row.status}</span></td>
        <td>{[row.location_id || '-', row.room_id || '-', row.asset_id || '-'].join(' / ')}</td><td>{row.assigned_to || '-'}</td>
        <td>{row.due_at ? new Date(row.due_at).toLocaleString() : '-'} {isOverdue(row) ? <span className="error-text">Overdue</span> : null}</td>
        <td>{row.resolved_at ? new Date(row.resolved_at).toLocaleString() : '-'}</td><td>{row.verified_at ? new Date(row.verified_at).toLocaleString() : '-'}</td>
        <td><ActionMenu id={row.id} status={row.status} onAction={onAction} busy={busy} /></td>
      </tr>)}
    </tbody></table></div>
  </>
}

function ActionMenu({ id, status, onAction, busy }: { id: number; status: SnaggingItem['status']; onAction: (id: number, action: 'assign' | 'start' | 'resolve' | 'verify' | 'reopen' | 'cancel' | 'void', payload: Record<string, unknown>) => Promise<void>; busy?: boolean }) {
  const actions = allowedSnagActions(status)
  const [pending, setPending] = useState<string | null>(null)
  const [reason, setReason] = useState('')
  const [assignee, setAssignee] = useState('')
  const requiresReason = pending === 'reopen' || pending === 'cancel' || pending === 'void'

  const confirm = async () => {
    if (!pending) return
    if (requiresReason && !reason.trim()) return
    if (pending === 'assign' && !assignee.trim()) return
    await onAction(id, pending as any, { reason: reason.trim(), assignee_id: assignee ? Number(assignee) : undefined })
    setPending(null)
    setReason('')
    setAssignee('')
  }

  return <>
    <div className="inline-actions">{actions.map((a) => <button key={a} className="button secondary small" disabled={busy} onClick={(e) => { e.stopPropagation(); if (['assign', 'verify', 'cancel', 'void', 'reopen'].includes(a)) setPending(a); else onAction(id, a, {}) }}>{a}</button>)}</div>
    {pending ? <div className="card-section" onClick={(e) => e.stopPropagation()}>
      {pending === 'assign' ? <input className="input" placeholder="Assignee ID" value={assignee} onChange={(e) => setAssignee(e.target.value)} /> : null}
      {requiresReason ? <textarea className="input" placeholder="Reason" value={reason} onChange={(e) => setReason(e.target.value)} /> : null}
      <button className="button secondary small" onClick={() => setPending(null)}>Cancel</button>
      <button className="button small" disabled={busy} onClick={confirm}>Confirm</button>
    </div> : null}
  </>
}
