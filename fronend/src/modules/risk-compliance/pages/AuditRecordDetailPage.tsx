import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { ApprovalTrail } from '../components/ApprovalTrail'
import { useApprovalTrail, useAuditRecordDetail, useCreateAuditRecord, useDecideApprovalTrail } from '../hooks/useRiskCompliance'

export function AuditRecordDetailPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const { id } = useParams()
  const isCreate = id === 'new' || !id
  const { data } = useAuditRecordDetail(auth?.accessToken, auth?.user?.org_id, !isCreate ? Number(id) : undefined)
  const createAudit = useCreateAuditRecord()
  const entityId = !isCreate ? Number(id) : undefined
  const { data: approvalTrail, reload: reloadTrail } = useApprovalTrail(auth?.accessToken, auth?.user?.org_id, 'audit_record', entityId ? String(entityId) : undefined)
  const decideApprovalTrail = useDecideApprovalTrail()
  const [error, setError] = useState('')
  const [form, setForm] = useState({ audit_code: '', title: '', scope: '', auditor: '', property_id: '', department_id: '', audit_date: '', result: 'PASS', score: '', findings_summary: '', corrective_actions_required: false, attachment_id: '' })

  useEffect(() => {
    if (!data) return
    setForm((prev) => ({ ...prev, audit_code: data.audit_code, findings_summary: data.findings_summary || '', score: data.score ? String(data.score) : '', corrective_actions_required: data.corrective_actions_required }))
  }, [data])

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!auth?.accessToken || !auth?.user?.org_id || !isCreate) return
    setError('')
    try {
      await createAudit(auth.accessToken, { org_id: auth.user.org_id, audit_code: form.audit_code.trim(), title: form.title.trim(), scope: form.scope.trim(), auditor: form.auditor.trim(), property_id: form.property_id ? Number(form.property_id) : null, department_id: form.department_id ? Number(form.department_id) : null, audit_date: form.audit_date || null, result: form.result, score: form.score ? Number(form.score) : null, findings_summary: form.findings_summary.trim(), corrective_actions_required: form.corrective_actions_required, attachment_id: form.attachment_id ? Number(form.attachment_id) : null })
      navigate('/risk-compliance/audit-records')
    } catch (err: any) {
      setError(err?.details?.detail || err?.message || 'Unable to create audit record.')
    }
  }

  return <div className="page full"><div className="glass panel"><h2>{isCreate ? 'New Audit Record' : `Audit Record #${id}`}</h2>{isCreate ? <form className="card-section" onSubmit={onSubmit}><div className="grid-form two"><label className="field">Audit Code<input className="input" value={form.audit_code} onChange={(e) => setForm((p) => ({ ...p, audit_code: e.target.value }))} required /></label><label className="field">Title<input className="input" value={form.title} onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))} required /></label><label className="field">Result<select className="input" value={form.result} onChange={(e) => setForm((p) => ({ ...p, result: e.target.value }))}><option value="PASS">PASS</option><option value="FAIL">FAIL</option><option value="PARTIAL">PARTIAL</option><option value="OBSERVATION">OBSERVATION</option></select></label><label className="field">Score<input className="input" type="number" step="0.01" value={form.score} onChange={(e) => setForm((p) => ({ ...p, score: e.target.value }))} /></label></div><label className="field">Findings Summary<textarea className="input" rows={3} value={form.findings_summary} onChange={(e) => setForm((p) => ({ ...p, findings_summary: e.target.value }))} /></label><label className="field"><input type="checkbox" checked={form.corrective_actions_required} onChange={(e) => setForm((p) => ({ ...p, corrective_actions_required: e.target.checked }))} /> Corrective actions required</label>{error ? <p className="error-text">{error}</p> : null}<button className="button" type="submit">Create Audit Record</button></form> : <><div className="card-section"><p><strong>Audit code:</strong> {data?.audit_code}</p><p><strong>Title:</strong> {data?.title || '-'}</p><p><strong>Scope:</strong> {data?.scope || '-'}</p><p><strong>Auditor:</strong> {data?.auditor || '-'}</p><p><strong>Result:</strong> {data?.result}</p><p><strong>Score:</strong> {data?.score ?? '-'}</p><h3>Findings Summary</h3><p>{data?.findings_summary || 'No findings summary.'}</p><p>{data?.corrective_actions_required ? 'Corrective actions required.' : 'No corrective actions required.'}</p><p>{data?.id ? <a href={`#attachment-${data.id}`}>Attachment link</a> : null}</p></div><ApprovalTrail entries={approvalTrail?.results || []} canManage={Boolean(auth?.user?.is_super_admin || auth?.user?.permissions?.includes('risk_compliance.approvals.manage'))} onApprove={() => void (async () => { if (!auth?.accessToken || !auth?.user?.org_id || !entityId) return; await decideApprovalTrail(auth.accessToken, { org_id: auth.user.org_id, entity_type: 'audit_record', entity_id: String(entityId), decision: 'APPROVE', comment: 'Audit sign-off approved' }); await reloadTrail() })()} onReject={() => void (async () => { if (!auth?.accessToken || !auth?.user?.org_id || !entityId) return; await decideApprovalTrail(auth.accessToken, { org_id: auth.user.org_id, entity_type: 'audit_record', entity_id: String(entityId), decision: 'REJECT', comment: 'Audit sign-off rejected' }); await reloadTrail() })()} /></>}</div></div>
}
