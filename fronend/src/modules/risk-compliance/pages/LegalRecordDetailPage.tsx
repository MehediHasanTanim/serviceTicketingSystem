import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { ApprovalTrail } from '../components/ApprovalTrail'
import { useApprovalTrail, useCreateLegalRecord, useDecideApprovalTrail, useLegalRecordDetail, useUpdateLegalRecord } from '../hooks/useRiskCompliance'

export function LegalRecordDetailPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const { id } = useParams()
  const isCreate = id === 'new' || !id
  const { data } = useLegalRecordDetail(auth?.accessToken, auth?.user?.org_id, !isCreate ? Number(id) : undefined)
  const createLegal = useCreateLegalRecord()
  const updateLegal = useUpdateLegalRecord()
  const entityId = !isCreate ? Number(id) : undefined
  const { data: approvalTrail, reload: reloadTrail } = useApprovalTrail(auth?.accessToken, auth?.user?.org_id, 'legal_record', entityId ? String(entityId) : undefined)
  const decideApprovalTrail = useDecideApprovalTrail()
  const [error, setError] = useState('')
  const [form, setForm] = useState({ record_code: '', title: '', description: '', record_type: 'CONTRACT', property_id: '', department_id: '', owner_id: '', vendor_name: '', effective_date: '', expiry_date: '', renewal_due_at: '', status: 'ACTIVE', attachment_id: '', notes: '' })

  useEffect(() => {
    if (!data) return
    setForm((prev) => ({ ...prev, record_code: data.record_code || '', status: data.status || 'ACTIVE', expiry_date: data.expiry_date || '', renewal_due_at: data.renewal_due_at ? data.renewal_due_at.slice(0, 16) : '' }))
  }, [data])

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!auth?.accessToken || !auth?.user?.org_id) return
    setError('')
    if (form.effective_date && form.expiry_date && new Date(form.expiry_date).getTime() <= new Date(form.effective_date).getTime()) {
      setError('Expiry date must be after effective date.')
      return
    }
    const payload = { org_id: auth.user.org_id, record_code: form.record_code.trim(), title: form.title.trim(), description: form.description.trim(), record_type: form.record_type, property_id: form.property_id ? Number(form.property_id) : null, department_id: form.department_id ? Number(form.department_id) : null, owner_id: form.owner_id ? Number(form.owner_id) : null, vendor_name: form.vendor_name.trim(), effective_date: form.effective_date || null, expiry_date: form.expiry_date || null, renewal_due_at: form.renewal_due_at ? new Date(form.renewal_due_at).toISOString() : null, status: form.status, attachment_id: form.attachment_id ? Number(form.attachment_id) : null, notes: form.notes.trim() }
    try {
      if (isCreate) await createLegal(auth.accessToken, payload)
      else await updateLegal(auth.accessToken, Number(id), payload)
      navigate('/risk-compliance/legal-records')
    } catch (err: any) {
      setError(err?.details?.detail || err?.message || 'Unable to save legal record.')
    }
  }

  return <div className="page full"><div className="glass panel"><h2>{isCreate ? 'New Legal Record' : `Legal Record #${id}`}</h2><form className="card-section" onSubmit={onSubmit}><div className="grid-form two"><label className="field">Record Code<input className="input" value={form.record_code} onChange={(e) => setForm((p) => ({ ...p, record_code: e.target.value }))} required /></label><label className="field">Title<input className="input" value={form.title} onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))} required /></label><label className="field">Type<select className="input" value={form.record_type} onChange={(e) => setForm((p) => ({ ...p, record_type: e.target.value }))}><option value="LEGAL">LEGAL</option><option value="CONTRACT">CONTRACT</option><option value="LICENSE">LICENSE</option><option value="PERMIT">PERMIT</option><option value="INSURANCE">INSURANCE</option><option value="AUDIT">AUDIT</option></select></label><label className="field">Vendor<input className="input" value={form.vendor_name} onChange={(e) => setForm((p) => ({ ...p, vendor_name: e.target.value }))} /></label><label className="field">Effective Date<input className="input" type="date" value={form.effective_date} onChange={(e) => setForm((p) => ({ ...p, effective_date: e.target.value }))} /></label><label className="field">Expiry Date<input className="input" type="date" value={form.expiry_date} onChange={(e) => setForm((p) => ({ ...p, expiry_date: e.target.value }))} /></label><label className="field">Renewal Due<input className="input" type="datetime-local" value={form.renewal_due_at} onChange={(e) => setForm((p) => ({ ...p, renewal_due_at: e.target.value }))} /></label><label className="field">Attachment ID<input className="input" value={form.attachment_id} onChange={(e) => setForm((p) => ({ ...p, attachment_id: e.target.value }))} /></label></div><label className="field">Description<textarea className="input" rows={2} value={form.description} onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))} /></label>{error ? <p className="error-text">{error}</p> : null}<button className="button" type="submit">Save Legal Record</button></form>
  <ApprovalTrail
    entries={approvalTrail?.results || []}
    canManage={Boolean(!isCreate && (auth?.user?.is_super_admin || auth?.user?.permissions?.includes('risk_compliance.approvals.manage')))}
    onApprove={() => void (async () => {
      if (!auth?.accessToken || !auth?.user?.org_id || !entityId) return
      await decideApprovalTrail(auth.accessToken, { org_id: auth.user.org_id, entity_type: 'legal_record', entity_id: String(entityId), decision: 'APPROVE', comment: 'Legal record approved' })
      await reloadTrail()
    })()}
    onReject={() => void (async () => {
      if (!auth?.accessToken || !auth?.user?.org_id || !entityId) return
      await decideApprovalTrail(auth.accessToken, { org_id: auth.user.org_id, entity_type: 'legal_record', entity_id: String(entityId), decision: 'REJECT', comment: 'Legal record rejected' })
      await reloadTrail()
    })()}
  />
  </div></div>
}
