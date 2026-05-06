import { useState } from 'react'
import type { SnagCategory, SnagSeverity, TechnicalAuditResult } from '../types/projects.types'

export function SnaggingForm({ orgId, onSubmit, saving, apiError }: { orgId: number; onSubmit: (payload: Record<string, unknown>) => Promise<void>; saving?: boolean; apiError?: string }) {
  const [form, setForm] = useState({ title: '', description: '', category: 'OTHER' as SnagCategory, severity: 'MEDIUM' as SnagSeverity, location_id: '', room_id: '', asset_id: '', assigned_to: '', due_at: '' })
  const [error, setError] = useState('')

  return <form className="card-section" onSubmit={async (e) => {
    e.preventDefault()
    if (!form.title.trim()) return setError('Title is required.')
    if (form.due_at && Number.isNaN(new Date(form.due_at).getTime())) return setError('Due date is invalid.')
    setError('')
    await onSubmit({ org_id: orgId, title: form.title.trim(), description: form.description.trim(), category: form.category, severity: form.severity, location_id: form.location_id ? Number(form.location_id) : null, room_id: form.room_id ? Number(form.room_id) : null, asset_id: form.asset_id ? Number(form.asset_id) : null, assigned_to: form.assigned_to ? Number(form.assigned_to) : null, due_at: form.due_at ? new Date(form.due_at).toISOString() : null })
  }}>
    <h3>Add Snagging Item</h3>
    {apiError || error ? <p className="error-text">{apiError || error}</p> : null}
    <div className="grid-form two"><input className="input" placeholder="Title" value={form.title} onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))} />
      <select className="input" value={form.category} onChange={(e) => setForm((p) => ({ ...p, category: e.target.value as SnagCategory }))}>{['FINISHING', 'ELECTRICAL', 'PLUMBING', 'HVAC', 'CIVIL', 'SAFETY', 'QUALITY', 'OTHER'].map((x) => <option key={x} value={x}>{x}</option>)}</select>
      <select className="input" value={form.severity} onChange={(e) => setForm((p) => ({ ...p, severity: e.target.value as SnagSeverity }))}>{['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((x) => <option key={x} value={x}>{x}</option>)}</select>
      <input className="input" placeholder="Assignee ID" value={form.assigned_to} onChange={(e) => setForm((p) => ({ ...p, assigned_to: e.target.value }))} />
      <input className="input" type="datetime-local" value={form.due_at} onChange={(e) => setForm((p) => ({ ...p, due_at: e.target.value }))} />
    </div>
    <textarea className="input" placeholder="Description" value={form.description} onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))} />
    <button className="button" disabled={saving}>{saving ? 'Saving...' : 'Create Snagging Item'}</button>
  </form>
}

export function TechnicalAuditForm({ orgId, onSubmit, saving, apiError }: { orgId: number; onSubmit: (payload: Record<string, unknown>) => Promise<void>; saving?: boolean; apiError?: string }) {
  const [form, setForm] = useState({ title: '', scope: '', auditor_id: '', conducted_at: '', score: '', result: '' as TechnicalAuditResult | '', findings_summary: '', corrective_actions_required: false })
  const [error, setError] = useState('')

  return <form className="card-section" onSubmit={async (e) => {
    e.preventDefault()
    if (!form.title.trim()) return setError('Title is required.')
    if (!form.auditor_id.trim()) return setError('Auditor is required.')
    if (form.score && (Number(form.score) < 0 || Number(form.score) > 100)) return setError('Score must be 0-100.')
    if ((form.result === 'FAIL' || form.result === 'PARTIAL') && !form.findings_summary.trim()) return setError('Findings summary is required for FAIL/PARTIAL.')
    setError('')
    await onSubmit({ org_id: orgId, title: form.title.trim(), scope: form.scope.trim(), auditor_id: Number(form.auditor_id), conducted_at: form.conducted_at ? new Date(form.conducted_at).toISOString() : null, score: form.score ? Number(form.score) : undefined, result: form.result || undefined, findings_summary: form.findings_summary.trim(), corrective_actions_required: form.corrective_actions_required })
  }}>
    <h3>Add Technical Audit</h3>
    {apiError || error ? <p className="error-text">{apiError || error}</p> : null}
    <div className="grid-form two"><input className="input" placeholder="Title" value={form.title} onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))} />
      <input className="input" placeholder="Auditor ID" value={form.auditor_id} onChange={(e) => setForm((p) => ({ ...p, auditor_id: e.target.value }))} />
      <input className="input" placeholder="Score" value={form.score} onChange={(e) => setForm((p) => ({ ...p, score: e.target.value }))} />
      <select className="input" value={form.result} onChange={(e) => setForm((p) => ({ ...p, result: e.target.value as TechnicalAuditResult | '' }))}><option value="">Result</option>{['PASS', 'FAIL', 'PARTIAL', 'OBSERVATION'].map((x) => <option key={x} value={x}>{x}</option>)}</select>
    </div>
    <textarea className="input" placeholder="Scope" value={form.scope} onChange={(e) => setForm((p) => ({ ...p, scope: e.target.value }))} />
    <textarea className="input" placeholder="Findings summary" value={form.findings_summary} onChange={(e) => setForm((p) => ({ ...p, findings_summary: e.target.value }))} />
    <label className="field inline"><input type="checkbox" checked={form.corrective_actions_required} onChange={(e) => setForm((p) => ({ ...p, corrective_actions_required: e.target.checked }))} />Corrective actions required</label>
    <button className="button" disabled={saving}>{saving ? 'Saving...' : 'Create Technical Audit'}</button>
  </form>
}
