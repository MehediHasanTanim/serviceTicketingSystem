import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { completeMitigation, createMitigation } from '../api/riskCompliance.api'
import { ApprovalTrail } from '../components/ApprovalTrail'
import { useApprovalTrail, useDecideApprovalTrail, useRiskDetail } from '../hooks/useRiskCompliance'

export function RiskDetailPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const { id } = useParams()
  const riskId = Number(id)
  const { data, loading, error, reload } = useRiskDetail(auth?.accessToken, auth?.user?.org_id, riskId)
  const { data: approvalTrail, reload: reloadTrail } = useApprovalTrail(auth?.accessToken, auth?.user?.org_id, 'risk', String(riskId))
  const decideApprovalTrail = useDecideApprovalTrail()
  const [form, setForm] = useState({ title: '', description: '', assigned_to: '', status: 'PENDING', due_at: '', effectiveness_score: '', notes: '' })
  const [completeNotes, setCompleteNotes] = useState('')

  const onCreateMitigation = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!auth?.accessToken || !auth?.user?.org_id) return
    await createMitigation(auth.accessToken, riskId, { org_id: auth.user.org_id, title: form.title.trim(), description: form.description.trim(), assigned_to: form.assigned_to ? Number(form.assigned_to) : null, status: form.status, due_at: form.due_at ? new Date(form.due_at).toISOString() : null, effectiveness_score: form.effectiveness_score ? Number(form.effectiveness_score) : null, notes: form.notes.trim() })
    setForm({ title: '', description: '', assigned_to: '', status: 'PENDING', due_at: '', effectiveness_score: '', notes: '' })
    await reload()
  }

  const onCompleteMitigation = async (mitigationId: number) => {
    if (!auth?.accessToken || !auth?.user?.org_id) return
    if (!completeNotes.trim()) return
    await completeMitigation(auth.accessToken, mitigationId, { org_id: auth.user.org_id, notes: completeNotes.trim() })
    setCompleteNotes('')
    await reload()
  }

  if (loading) return <div className="page full"><div className="glass panel"><p>Loading risk detail...</p></div></div>
  if (error || !data?.risk) return <div className="page full"><div className="glass panel"><p className="error-text">{error || 'Risk not found.'}</p></div></div>

  return <div className="page full"><div className="glass panel"><div className="section-head"><h2>{data.risk.title}</h2><button className="button secondary" onClick={() => navigate(`/risk-compliance/risks/${riskId}/edit`)}>Edit</button></div>
    <p><strong>Risk code:</strong> {data.risk.risk_code}</p><p><strong>Level:</strong> {data.risk.risk_level} ({data.risk.inherent_score})</p><p><strong>Status:</strong> {data.risk.status}</p>
    <div className="card-section"><h3>Mitigation Tracking</h3>
      <div className="table-wrap"><table className="data-table"><thead><tr><th>Title</th><th>Status</th><th>Due At</th><th>Assigned To</th><th>Effectiveness</th><th>Action</th></tr></thead><tbody>{data.mitigations.map((m) => { const overdue = Boolean(m.due_at && new Date(m.due_at).getTime() < Date.now() && m.status !== 'COMPLETED'); return <tr key={m.id}><td>{m.title}</td><td>{m.status}</td><td>{m.due_at ? new Date(m.due_at).toLocaleString() : '-'} {overdue ? <span className="badge critical">Overdue</span> : null}</td><td>{m.assigned_to || '-'}</td><td>{m.effectiveness_score ?? '-'}</td><td>{m.status !== 'COMPLETED' ? <button className="button secondary small" onClick={() => void onCompleteMitigation(m.id)}>Complete</button> : '-'}</td></tr> })}</tbody></table></div>
      <label className="field">Completion Notes (required by policy)<textarea className="input" rows={2} value={completeNotes} onChange={(e) => setCompleteNotes(e.target.value)} /></label>
    </div>
    <form className="card-section" onSubmit={onCreateMitigation}><h3>Create Mitigation Action</h3><div className="grid-form two"><label className="field">Title<input className="input" value={form.title} onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))} required /></label><label className="field">Assigned To<input className="input" value={form.assigned_to} onChange={(e) => setForm((p) => ({ ...p, assigned_to: e.target.value }))} /></label><label className="field">Due At<input className="input" type="datetime-local" value={form.due_at} onChange={(e) => setForm((p) => ({ ...p, due_at: e.target.value }))} /></label><label className="field">Effectiveness Score<input className="input" type="number" value={form.effectiveness_score} onChange={(e) => setForm((p) => ({ ...p, effectiveness_score: e.target.value }))} /></label></div><label className="field">Description<textarea className="input" rows={2} value={form.description} onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))} /></label><label className="field">Notes<textarea className="input" rows={2} value={form.notes} onChange={(e) => setForm((p) => ({ ...p, notes: e.target.value }))} /></label><button className="button" type="submit">Create Mitigation</button></form>
    <ApprovalTrail
      entries={approvalTrail?.results || []}
      canManage={Boolean(auth?.user?.is_super_admin || auth?.user?.permissions?.includes('risk_compliance.approvals.manage'))}
      onApprove={() => void (async () => {
        if (!auth?.accessToken || !auth?.user?.org_id) return
        await decideApprovalTrail(auth.accessToken, { org_id: auth.user.org_id, entity_type: 'risk', entity_id: String(riskId), decision: 'APPROVE', comment: 'Risk accepted' })
        await reloadTrail()
      })()}
      onReject={() => void (async () => {
        if (!auth?.accessToken || !auth?.user?.org_id) return
        await decideApprovalTrail(auth.accessToken, { org_id: auth.user.org_id, entity_type: 'risk', entity_id: String(riskId), decision: 'REJECT', comment: 'Risk rejected' })
        await reloadTrail()
      })()}
    />
  </div></div>
}
