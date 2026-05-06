import { useState } from 'react'
import type { Project, ProjectPriority, ProjectStatus, ProjectType } from '../types/projects.types'

type Props = {
  orgId: number
  mode: 'create' | 'edit'
  initial?: Project
  saving?: boolean
  apiError?: string
  onSubmit: (payload: Record<string, unknown>) => Promise<void> | void
}

const types: ProjectType[] = ['RENOVATION', 'CONSTRUCTION', 'MAINTENANCE_UPGRADE', 'COMPLIANCE_REMEDIATION', 'TECHNOLOGY', 'OTHER']
const priorities: ProjectPriority[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
const statuses: ProjectStatus[] = ['DRAFT', 'PLANNED', 'IN_PROGRESS', 'ON_HOLD', 'COMPLETED', 'CANCELLED', 'VOID']

export function ProjectForm({ orgId, mode, initial, saving, apiError, onSubmit }: Props) {
  const [form, setForm] = useState({
    title: initial?.title || '', description: initial?.description || '', property_id: initial?.property_id ? String(initial.property_id) : '', department_id: initial?.department_id ? String(initial.department_id) : '',
    project_type: (initial?.project_type || 'OTHER') as ProjectType, priority: (initial?.priority || 'MEDIUM') as ProjectPriority, owner_id: initial?.owner_id ? String(initial.owner_id) : '', manager_id: initial?.manager_id ? String(initial.manager_id) : '',
    start_date: initial?.start_date || '', planned_end_date: initial?.planned_end_date || '', actual_end_date: initial?.actual_end_date || '', budget_amount: initial?.budget_amount || '0.00', actual_cost: initial?.actual_cost || '0.00', progress_percentage: String(initial?.progress_percentage ?? 0), status: (initial?.status || 'DRAFT') as ProjectStatus,
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const update = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => setForm((p) => ({ ...p, [k]: e.target.value }))
  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    const next: Record<string, string> = {}
    if (!form.title.trim()) next.title = 'Title is required.'
    if (!form.project_type) next.project_type = 'Project type is required.'
    if (!form.priority) next.priority = 'Priority is required.'
    if (form.start_date && form.planned_end_date && new Date(form.planned_end_date).getTime() < new Date(form.start_date).getTime()) next.planned_end_date = 'Planned end date must be after start date.'
    if (form.status === 'COMPLETED' && !form.actual_end_date) next.actual_end_date = 'Actual end date is required when completed.'
    if (Number(form.progress_percentage) < 0 || Number(form.progress_percentage) > 100) next.progress_percentage = 'Progress must be 0-100.'
    if (Number(form.budget_amount) < 0) next.budget_amount = 'Budget cannot be negative.'
    if (Number(form.actual_cost) < 0) next.actual_cost = 'Actual cost cannot be negative.'
    setErrors(next)
    if (Object.keys(next).length) return

    await onSubmit({
      org_id: orgId,
      title: form.title.trim(), description: form.description.trim(), property_id: form.property_id ? Number(form.property_id) : null, department_id: form.department_id ? Number(form.department_id) : null,
      project_type: form.project_type, priority: form.priority, owner_id: form.owner_id ? Number(form.owner_id) : null, manager_id: form.manager_id ? Number(form.manager_id) : null,
      start_date: form.start_date || null, planned_end_date: form.planned_end_date || null, actual_end_date: form.actual_end_date || null,
      budget_amount: form.budget_amount, actual_cost: form.actual_cost, progress_percentage: Number(form.progress_percentage), status: form.status,
    })
  }

  return <form className="card-section" onSubmit={submit} aria-label="Project Form"><h3>{mode === 'create' ? 'New Project' : 'Edit Project'}</h3>
    {apiError ? <p className="error-text">{apiError}</p> : null}
    <div className="grid-form two">
      <label className="field">Title<input aria-label="Title" className="input" value={form.title} onChange={update('title')} />{errors.title ? <span className="error-text">{errors.title}</span> : null}</label>
      <label className="field">Type<select className="input" value={form.project_type} onChange={update('project_type')}>{types.map((v) => <option key={v} value={v}>{v}</option>)}</select></label>
      <label className="field">Priority<select className="input" value={form.priority} onChange={update('priority')}>{priorities.map((v) => <option key={v} value={v}>{v}</option>)}</select></label>
      <label className="field">Status<select className="input" value={form.status} onChange={update('status')}>{statuses.map((v) => <option key={v} value={v}>{v}</option>)}</select></label>
      <label className="field">Property ID<input className="input" value={form.property_id} onChange={update('property_id')} /></label>
      <label className="field">Department ID<input className="input" value={form.department_id} onChange={update('department_id')} /></label>
      <label className="field">Owner ID<input className="input" value={form.owner_id} onChange={update('owner_id')} /></label>
      <label className="field">Manager ID<input className="input" value={form.manager_id} onChange={update('manager_id')} /></label>
      <label className="field">Start date<input aria-label="Start date" type="date" className="input" value={form.start_date || ''} onChange={update('start_date')} /></label>
      <label className="field">Planned end date<input aria-label="Planned end date" type="date" className="input" value={form.planned_end_date || ''} onChange={update('planned_end_date')} />{errors.planned_end_date ? <span className="error-text">{errors.planned_end_date}</span> : null}</label>
      <label className="field">Actual end date<input aria-label="Actual end date" type="date" className="input" value={form.actual_end_date || ''} onChange={update('actual_end_date')} />{errors.actual_end_date ? <span className="error-text">{errors.actual_end_date}</span> : null}</label>
      <label className="field">Progress %<input aria-label="Progress %" className="input" value={form.progress_percentage} onChange={update('progress_percentage')} />{errors.progress_percentage ? <span className="error-text">{errors.progress_percentage}</span> : null}</label>
      <label className="field">Budget<input className="input" value={form.budget_amount} onChange={update('budget_amount')} />{errors.budget_amount ? <span className="error-text">{errors.budget_amount}</span> : null}</label>
      <label className="field">Actual cost<input className="input" value={form.actual_cost} onChange={update('actual_cost')} />{errors.actual_cost ? <span className="error-text">{errors.actual_cost}</span> : null}</label>
    </div>
    <label className="field">Description<textarea className="input" rows={4} value={form.description} onChange={update('description')} /></label>
    <button className="button" disabled={saving}>{saving ? 'Saving...' : mode === 'create' ? 'Create' : 'Update'}</button>
  </form>
}
