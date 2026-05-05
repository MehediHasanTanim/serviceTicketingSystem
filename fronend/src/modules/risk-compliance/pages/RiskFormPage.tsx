import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useCreateRisk, useRiskDetail, useUpdateRisk } from '../hooks/useRiskCompliance'

function riskLevel(score: number) {
  if (score >= 17) return 'CRITICAL'
  if (score >= 10) return 'HIGH'
  if (score >= 5) return 'MEDIUM'
  return 'LOW'
}

export function RiskFormPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const { id } = useParams()
  const isEdit = Boolean(id)
  const { data } = useRiskDetail(auth?.accessToken, auth?.user?.org_id, id ? Number(id) : undefined)
  const createRisk = useCreateRisk()
  const updateRisk = useUpdateRisk()
  const [error, setError] = useState('')
  const [form, setForm] = useState({ risk_code: '', title: '', description: '', category: '', property_id: '', department_id: '', owner_id: '', likelihood: '1', impact: '1', status: 'OPEN', identified_at: '', reviewed_at: '', due_at: '' })
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (!data?.risk) return
    const risk = data.risk
    setForm({ risk_code: risk.risk_code, title: risk.title, description: risk.description || '', category: risk.category || '', property_id: risk.property_id ? String(risk.property_id) : '', department_id: risk.department_id ? String(risk.department_id) : '', owner_id: risk.owner_id ? String(risk.owner_id) : '', likelihood: String(risk.likelihood), impact: String(risk.impact), status: risk.status, identified_at: risk.identified_at ? risk.identified_at.slice(0, 16) : '', reviewed_at: risk.reviewed_at ? risk.reviewed_at.slice(0, 16) : '', due_at: risk.due_at ? risk.due_at.slice(0, 16) : '' })
  }, [data])

  const inherentScore = useMemo(() => Number(form.likelihood || 0) * Number(form.impact || 0), [form.likelihood, form.impact])

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!auth?.accessToken || !auth?.user?.org_id) return
    const nextErrors: Record<string, string> = {}
    if (!form.title.trim()) nextErrors.title = 'Title is required.'
    if (!isEdit && !form.risk_code.trim()) nextErrors.risk_code = 'Risk code is required.'
    if (Number(form.likelihood) < 1 || Number(form.likelihood) > 5) nextErrors.likelihood = 'Likelihood must be between 1 and 5.'
    if (Number(form.impact) < 1 || Number(form.impact) > 5) nextErrors.impact = 'Impact must be between 1 and 5.'
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) return

    const payload = { org_id: auth.user.org_id, risk_code: form.risk_code.trim(), title: form.title.trim(), description: form.description.trim(), category: form.category.trim(), property_id: form.property_id ? Number(form.property_id) : null, department_id: form.department_id ? Number(form.department_id) : null, owner_id: form.owner_id ? Number(form.owner_id) : null, likelihood: Number(form.likelihood), impact: Number(form.impact), status: form.status, identified_at: form.identified_at ? new Date(form.identified_at).toISOString() : undefined, reviewed_at: form.reviewed_at ? new Date(form.reviewed_at).toISOString() : null, due_at: form.due_at ? new Date(form.due_at).toISOString() : null }

    setError('')
    try {
      if (isEdit && id) await updateRisk(auth.accessToken, Number(id), payload)
      else await createRisk(auth.accessToken, payload)
      navigate('/risk-compliance/risks')
    } catch (err: any) {
      setError(err?.details?.detail || err?.message || 'Unable to save risk.')
    }
  }

  return <div className="page full"><div className="glass panel"><h2>{isEdit ? 'Edit Risk' : 'New Risk'}</h2><form className="card-section" onSubmit={onSubmit} aria-label="Risk form">
    <div className="grid-form two">
      {!isEdit ? <label className="field">Risk Code<input className="input" value={form.risk_code} onChange={(e) => setForm((p) => ({ ...p, risk_code: e.target.value }))} />{errors.risk_code ? <span className="error-text">{errors.risk_code}</span> : null}</label> : null}
      <label className="field">Title<input className="input" value={form.title} onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))} />{errors.title ? <span className="error-text">{errors.title}</span> : null}</label>
      <label className="field">Category<input className="input" value={form.category} onChange={(e) => setForm((p) => ({ ...p, category: e.target.value }))} /></label>
      <label className="field">Status<select className="input" value={form.status} onChange={(e) => setForm((p) => ({ ...p, status: e.target.value }))}><option value="OPEN">OPEN</option><option value="MITIGATING">MITIGATING</option><option value="MONITORING">MONITORING</option><option value="ACCEPTED">ACCEPTED</option><option value="CLOSED">CLOSED</option><option value="VOID">VOID</option></select></label>
      <label className="field">Likelihood (1-5)<input className="input" type="number" min={1} max={5} value={form.likelihood} onChange={(e) => setForm((p) => ({ ...p, likelihood: e.target.value }))} />{errors.likelihood ? <span className="error-text">{errors.likelihood}</span> : null}</label>
      <label className="field">Impact (1-5)<input className="input" type="number" min={1} max={5} value={form.impact} onChange={(e) => setForm((p) => ({ ...p, impact: e.target.value }))} />{errors.impact ? <span className="error-text">{errors.impact}</span> : null}</label>
      <label className="field">Inherent Score<input className="input" value={String(inherentScore)} readOnly /></label>
      <label className="field">Risk Level<input className="input" value={riskLevel(inherentScore)} readOnly /></label>
      <label className="field">Identified At<input className="input" type="datetime-local" value={form.identified_at} onChange={(e) => setForm((p) => ({ ...p, identified_at: e.target.value }))} /></label>
      <label className="field">Reviewed At<input className="input" type="datetime-local" value={form.reviewed_at} onChange={(e) => setForm((p) => ({ ...p, reviewed_at: e.target.value }))} /></label>
      <label className="field">Due At<input className="input" type="datetime-local" value={form.due_at} onChange={(e) => setForm((p) => ({ ...p, due_at: e.target.value }))} /></label>
    </div>
    <label className="field">Description<textarea className="input" rows={3} value={form.description} onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))} /></label>
    {error ? <p className="error-text">{error}</p> : null}
    <button className="button" type="submit">Save Risk</button>
  </form></div></div>
}
