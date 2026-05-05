import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useComplianceRequirementDetail, useCreateComplianceRequirement, useUpdateComplianceRequirement } from '../hooks/useRiskCompliance'
import type { ComplianceChecklistItem } from '../types/riskCompliance.types'

export function ComplianceRequirementFormPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const { id } = useParams()
  const isEdit = Boolean(id)
  const { data } = useComplianceRequirementDetail(auth?.accessToken, auth?.user?.org_id, id ? Number(id) : undefined)
  const createRequirement = useCreateComplianceRequirement()
  const updateRequirement = useUpdateComplianceRequirement()
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({ requirement_code: '', title: '', description: '', category: '', regulation_reference: '', property_id: '', department_id: '', owner_id: '', frequency_type: 'MONTHLY', frequency_interval: '1', priority: 'MEDIUM', effective_date: '', expiry_date: '', status: 'ACTIVE' })
  const [items, setItems] = useState<ComplianceChecklistItem[]>([{ title: '', description: '', is_required: true, evidence_required: false, sort_order: 1 }])
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (!data) return
    setForm({ requirement_code: data.requirement_code, title: data.title, description: data.description || '', category: data.category || '', regulation_reference: data.regulation_reference || '', property_id: data.property_id ? String(data.property_id) : '', department_id: data.department_id ? String(data.department_id) : '', owner_id: data.owner_id ? String(data.owner_id) : '', frequency_type: data.frequency_type, frequency_interval: String(data.frequency_interval || 1), priority: data.priority, effective_date: data.effective_date || '', expiry_date: data.expiry_date || '', status: data.status })
    setItems(data.checklist_items.length ? data.checklist_items : [{ title: '', description: '', is_required: true, evidence_required: false, sort_order: 1 }])
  }, [data])

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!auth?.accessToken || !auth?.user?.org_id) return
    const nextErrors: Record<string, string> = {}
    if (!form.title.trim()) nextErrors.title = 'Title is required.'
    if (!isEdit && !form.requirement_code.trim()) nextErrors.requirement_code = 'Requirement code is required.'
    if (!form.frequency_type.trim()) nextErrors.frequency_type = 'Frequency type is required.'
    if (form.frequency_type === 'CUSTOM' && (!form.frequency_interval || Number(form.frequency_interval) < 1)) nextErrors.frequency_interval = 'Custom interval must be greater than 0.'
    if (form.effective_date && form.expiry_date && new Date(form.expiry_date).getTime() <= new Date(form.effective_date).getTime()) nextErrors.expiry_date = 'Expiry date must be after effective date.'
    if (items.some((item) => !item.title.trim())) nextErrors.checklist_items = 'Checklist item title is required.'
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) return

    setSaving(true)
    setError('')
    const payload = {
      org_id: auth.user.org_id,
      requirement_code: form.requirement_code.trim(),
      title: form.title.trim(),
      description: form.description.trim(),
      category: form.category.trim(),
      regulation_reference: form.regulation_reference.trim(),
      property_id: form.property_id ? Number(form.property_id) : null,
      department_id: form.department_id ? Number(form.department_id) : null,
      owner_id: form.owner_id ? Number(form.owner_id) : null,
      frequency_type: form.frequency_type,
      frequency_interval: Number(form.frequency_interval || 1),
      priority: form.priority,
      effective_date: form.effective_date || null,
      expiry_date: form.expiry_date || null,
      status: form.status,
      checklist_items: items.map((item, idx) => ({ ...item, title: item.title.trim(), description: item.description.trim(), sort_order: idx + 1 })),
    }

    try {
      if (isEdit && id) await updateRequirement(auth.accessToken, Number(id), payload)
      else await createRequirement(auth.accessToken, payload)
      navigate('/risk-compliance/requirements')
    } catch (err: any) {
      setError(err?.details?.detail || err?.message || 'Unable to save requirement.')
    } finally {
      setSaving(false)
    }
  }

  return <div className="page full"><div className="glass panel"><h2>{isEdit ? 'Edit Compliance Requirement' : 'New Compliance Requirement'}</h2><form className="card-section" onSubmit={onSubmit} aria-label="Compliance requirement form">
    <div className="grid-form two">
      {!isEdit ? <label className="field">Requirement Code<input className="input" value={form.requirement_code} onChange={(e) => setForm((p) => ({ ...p, requirement_code: e.target.value }))} />{errors.requirement_code ? <span className="error-text">{errors.requirement_code}</span> : null}</label> : null}
      <label className="field">Title<input className="input" value={form.title} onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))} />{errors.title ? <span className="error-text">{errors.title}</span> : null}</label>
      <label className="field">Category<input className="input" value={form.category} onChange={(e) => setForm((p) => ({ ...p, category: e.target.value }))} /></label>
      <label className="field">Regulation Reference<input className="input" value={form.regulation_reference} onChange={(e) => setForm((p) => ({ ...p, regulation_reference: e.target.value }))} /></label>
      <label className="field">Frequency<select className="input" value={form.frequency_type} onChange={(e) => setForm((p) => ({ ...p, frequency_type: e.target.value }))}><option value="DAILY">DAILY</option><option value="WEEKLY">WEEKLY</option><option value="MONTHLY">MONTHLY</option><option value="QUARTERLY">QUARTERLY</option><option value="YEARLY">YEARLY</option><option value="CUSTOM">CUSTOM</option></select></label>
      <label className="field">Frequency Interval<input className="input" type="number" min={1} value={form.frequency_interval} onChange={(e) => setForm((p) => ({ ...p, frequency_interval: e.target.value }))} />{errors.frequency_interval ? <span className="error-text">{errors.frequency_interval}</span> : null}</label>
      <label className="field">Priority<select className="input" value={form.priority} onChange={(e) => setForm((p) => ({ ...p, priority: e.target.value }))}><option value="LOW">LOW</option><option value="MEDIUM">MEDIUM</option><option value="HIGH">HIGH</option><option value="CRITICAL">CRITICAL</option></select></label>
      <label className="field">Status<select className="input" value={form.status} onChange={(e) => setForm((p) => ({ ...p, status: e.target.value }))}><option value="ACTIVE">ACTIVE</option><option value="INACTIVE">INACTIVE</option><option value="ARCHIVED">ARCHIVED</option></select></label>
      <label className="field">Effective Date<input className="input" type="date" value={form.effective_date} onChange={(e) => setForm((p) => ({ ...p, effective_date: e.target.value }))} /></label>
      <label className="field">Expiry Date<input className="input" type="date" value={form.expiry_date} onChange={(e) => setForm((p) => ({ ...p, expiry_date: e.target.value }))} />{errors.expiry_date ? <span className="error-text">{errors.expiry_date}</span> : null}</label>
    </div>
    <label className="field">Description<textarea className="input" rows={3} value={form.description} onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))} /></label>
    <div className="section-head"><h3>Checklist Items</h3><button type="button" className="button secondary small" onClick={() => setItems((prev) => [...prev, { title: '', description: '', is_required: true, evidence_required: false, sort_order: prev.length + 1 }])}>Add Item</button></div>
    {items.map((item, index) => <div key={index} className="grid-form two card-section"><label className="field">Item Title<input className="input" value={item.title} onChange={(e) => setItems((prev) => prev.map((row, i) => i === index ? { ...row, title: e.target.value } : row))} /></label><label className="field">Description<input className="input" value={item.description} onChange={(e) => setItems((prev) => prev.map((row, i) => i === index ? { ...row, description: e.target.value } : row))} /></label><label className="field"><input type="checkbox" checked={item.is_required} onChange={(e) => setItems((prev) => prev.map((row, i) => i === index ? { ...row, is_required: e.target.checked } : row))} /> Required</label><label className="field"><input type="checkbox" checked={item.evidence_required} onChange={(e) => setItems((prev) => prev.map((row, i) => i === index ? { ...row, evidence_required: e.target.checked } : row))} /> Evidence Required</label><button type="button" className="button secondary small" onClick={() => setItems((prev) => prev.filter((_, i) => i !== index))}>Remove</button></div>)}
    {errors.checklist_items ? <p className="error-text">{errors.checklist_items}</p> : null}
    {error ? <p className="error-text">{error}</p> : null}
    <button className="button" type="submit" disabled={saving}>{saving ? 'Saving...' : 'Save Requirement'}</button>
  </form></div></div>
}
