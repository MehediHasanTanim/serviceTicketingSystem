import { useState } from 'react'
import type { TechnicalAudit } from '../types/projects.types'
import { allowedAuditActions } from './utils'

export function TechnicalAudits({ items, onOpen, onAction, busy }: { items: TechnicalAudit[]; onOpen: (id: number) => void; onAction: (id: number, action: 'start' | 'complete' | 'cancel' | 'void', payload: Record<string, unknown>) => Promise<void>; busy?: boolean }) {
  return <div className="table-wrap"><table className="data-table"><thead><tr><th>Audit Number</th><th>Title</th><th>Auditor</th><th>Status</th><th>Result</th><th>Score</th><th>Conducted At</th><th>Completed At</th><th>Corrective Actions Required</th><th>Actions</th></tr></thead><tbody>
    {items.map((row) => <tr key={row.id} onClick={() => onOpen(row.id)}>
      <td>{row.audit_number}</td><td>{row.title}</td><td>{row.auditor_id || '-'}</td><td><span className="badge neutral">{row.status}</span></td><td>{row.result || '-'}</td><td>{row.score ?? '-'}</td><td>{row.conducted_at ? new Date(row.conducted_at).toLocaleString() : '-'}</td><td>{row.completed_at ? new Date(row.completed_at).toLocaleString() : '-'}</td><td>{row.corrective_actions_required ? 'Yes' : 'No'}</td>
      <td><AuditActionMenu row={row} onAction={onAction} busy={busy} /></td>
    </tr>)}
  </tbody></table></div>
}

function AuditActionMenu({ row, onAction, busy }: { row: TechnicalAudit; onAction: (id: number, action: 'start' | 'complete' | 'cancel' | 'void', payload: Record<string, unknown>) => Promise<void>; busy?: boolean }) {
  const actions = allowedAuditActions(row.status)
  const [pending, setPending] = useState<string | null>(null)
  const [result, setResult] = useState('')
  const [score, setScore] = useState('')
  const [findings, setFindings] = useState('')
  const [autoCreate, setAutoCreate] = useState(false)

  const confirm = async () => {
    if (!pending) return
    const payload: Record<string, unknown> = {}
    if (pending === 'complete') {
      if (result) payload.result = result
      if (score) payload.score = Number(score)
      if (findings) payload.findings_summary = findings
      payload.auto_create_corrective_item = autoCreate
    }
    await onAction(row.id, pending as any, payload)
    setPending(null)
  }

  return <>
    <div className="inline-actions">{actions.map((a) => <button key={a} className="button secondary small" disabled={busy} onClick={(e) => { e.stopPropagation(); if (['complete', 'cancel', 'void'].includes(a)) setPending(a); else onAction(row.id, a, {}) }}>{a}</button>)}</div>
    {pending ? <div className="card-section" onClick={(e) => e.stopPropagation()}>
      {pending === 'complete' ? <><select className="input" value={result} onChange={(e) => setResult(e.target.value)}><option value="">Result</option>{['PASS', 'FAIL', 'PARTIAL', 'OBSERVATION'].map((x) => <option key={x} value={x}>{x}</option>)}</select>
        <input className="input" placeholder="Score" value={score} onChange={(e) => setScore(e.target.value)} />
        <textarea className="input" placeholder="Findings summary" value={findings} onChange={(e) => setFindings(e.target.value)} />
        {(result === 'FAIL' || result === 'PARTIAL') ? <label className="field inline"><input type="checkbox" checked={autoCreate} onChange={(e) => setAutoCreate(e.target.checked)} />Create corrective snagging item</label> : null}
      </> : null}
      <button className="button secondary small" onClick={() => setPending(null)}>Cancel</button>
      <button className="button small" disabled={busy} onClick={confirm}>Confirm</button>
    </div> : null}
  </>
}
