import { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useOutletReadinessAction, useOutletReadinessDetail, useUpdateOutletReadiness } from '../hooks/useFoodBeverage'
import type { ChecklistCategory, ChecklistResult } from '../types/foodBeverage.types'

export function OutletReadinessDetailPage() {
  const { id } = useParams(); const { auth } = useAuth(); const [busy, setBusy] = useState(false); const [err, setErr] = useState(''); const [confirm, setConfirm] = useState<'verify'|'void'|''>('')
  const detail = useOutletReadinessDetail(auth?.accessToken, auth?.user?.org_id, Number(id)); const action = useOutletReadinessAction(); const update = useUpdateOutletReadiness()
  const groups = useMemo(() => (detail.data?.checklist_items || []).reduce((acc, item) => { (acc[item.category] ||= []).push(item); return acc }, {} as Record<ChecklistCategory, any[]>), [detail.data])

  const saveItem = async (itemId: number, result: ChecklistResult, comment: string) => {
    if (!auth?.accessToken || !id) return
    if (result === 'FAIL' && !comment.trim()) { setErr('FAIL item requires comment.'); return }
    setBusy(true); setErr('')
    try { await update(auth.accessToken, Number(id), { org_id: auth.user?.org_id, checklist_item_id: itemId, result, comment }); await detail.reload() } catch (e: any) { setErr(e.message || 'Failed to update checklist item') } finally { setBusy(false) }
  }
  const runAction = async (a: 'start'|'submit'|'verify'|'void', reason?: string) => {
    if (!auth?.accessToken || !id) return
    setBusy(true); setErr('')
    try { await action(auth.accessToken, Number(id), a, { org_id: auth.user?.org_id, reason }); setConfirm(''); await detail.reload() } catch (e: any) { setErr(e.message || 'Failed action') } finally { setBusy(false) }
  }

  return <div className="page full"><div className="glass panel"><h2>Outlet Readiness Detail</h2>
    {detail.loading ? <p>Loading...</p> : null}{detail.error ? <p className="error-text">{detail.error}</p> : null}{err ? <p className="error-text">{err}</p> : null}
    {detail.data ? <>
      <div className="row-actions"><button className="button small" disabled={busy} onClick={() => void runAction('start')}>Start readiness check</button><button className="button small" disabled={busy} onClick={() => void runAction('submit')}>Submit readiness check</button><button className="button secondary small" disabled={busy} onClick={() => setConfirm('verify')}>Verify readiness</button><button className="button secondary small" disabled={busy} onClick={() => setConfirm('void')}>Void readiness</button></div>
      {Object.entries(groups).map(([category, items]) => <div className="card-section" key={category}><h3>{category}</h3><div className="table-wrap"><table className="data-table"><thead><tr><th>Item</th><th>Result</th><th>Comment</th><th>Completed By</th><th>Completed At</th></tr></thead><tbody>{(items || []).map((x: any) => <tr key={x.id}><td>{x.name}</td><td><select className="input" aria-label={`result-${x.id}`} disabled={busy} value={x.result || ''} onChange={(e) => void saveItem(x.id, e.target.value as ChecklistResult, x.comment || '')}><option value="">Select</option><option value="PASS">PASS</option><option value="FAIL">FAIL</option><option value="N/A">N/A</option></select></td><td><input className="input" aria-label={`comment-${x.id}`} defaultValue={x.comment || ''} onBlur={(e) => void saveItem(x.id, (x.result || 'PASS') as ChecklistResult, e.target.value)} /></td><td>{x.completed_by || '-'}</td><td>{x.completed_at ? new Date(x.completed_at).toLocaleString() : '-'}</td></tr>)}</tbody></table></div></div>)}
    </> : null}
    {confirm ? <div className="modal-backdrop" role="presentation"><div className="modal" role="dialog" aria-modal="true" aria-label="Readiness confirmation"><p>Confirm {confirm} action?</p><div className="modal-actions"><button className="button secondary small" onClick={() => setConfirm('')}>Cancel</button><button className="button small" onClick={() => void runAction(confirm)}>Confirm</button></div></div></div> : null}
  </div></div>
}
