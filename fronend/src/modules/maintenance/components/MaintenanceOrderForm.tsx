import { useState } from 'react'
import type { MaintenanceOrder, MaintenanceTaskType, Priority } from '../types/maintenance.types'
import { toIsoOrNull } from './utils'

type Props = {
  orgId: number
  mode: 'create' | 'edit'
  initial?: MaintenanceOrder | null
  prefilledAssetId?: number | null
  onSubmit: (payload: Record<string, unknown>) => Promise<void> | void
  saving?: boolean
}

export function MaintenanceOrderForm({ orgId, mode, initial, prefilledAssetId, onSubmit, saving }: Props) {
  const [form, setForm] = useState({
    task_type: (initial?.task_type || 'CORRECTIVE') as MaintenanceTaskType,
    title: initial?.title || '',
    description: initial?.description || '',
    asset_id: initial?.asset_id ? String(initial.asset_id) : (prefilledAssetId ? String(prefilledAssetId) : ''),
    room_id: initial?.room_id ? String(initial.room_id) : '',
    property_id: initial?.property_id ? String(initial.property_id) : '',
    department_id: initial?.department_id ? String(initial.department_id) : '',
    priority: (initial?.priority || 'MEDIUM') as Priority,
    assigned_to: initial?.assigned_to ? String(initial.assigned_to) : '',
    scheduled_at: initial?.scheduled_at ? initial.scheduled_at.slice(0, 16) : '',
    due_at: initial?.due_at ? initial.due_at.slice(0, 16) : '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const update = (key: keyof typeof form) => (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setForm((prev) => ({ ...prev, [key]: event.target.value }))
  }

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    const nextErrors: Record<string, string> = {}
    if (!form.title.trim()) nextErrors.title = 'Title is required.'
    if (form.scheduled_at && form.due_at && new Date(form.scheduled_at).getTime() > new Date(form.due_at).getTime()) {
      nextErrors.due_at = 'Due date must be after schedule date.'
    }
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) return

    await onSubmit({
      org_id: orgId,
      task_type: form.task_type,
      title: form.title.trim(),
      description: form.description.trim(),
      asset_id: form.asset_id ? Number(form.asset_id) : null,
      room_id: form.room_id ? Number(form.room_id) : null,
      property_id: form.property_id ? Number(form.property_id) : null,
      department_id: form.department_id ? Number(form.department_id) : null,
      priority: form.priority,
      assigned_to: form.assigned_to ? Number(form.assigned_to) : null,
      scheduled_at: toIsoOrNull(form.scheduled_at),
      due_at: toIsoOrNull(form.due_at),
    })
  }

  return (
    <form className="card-section" onSubmit={submit} aria-label="Maintenance order form">
      <div className="grid-form two">
        <label className="field">Type
          <select className="input" value={form.task_type} onChange={update('task_type')}>
            <option value="CORRECTIVE">CORRECTIVE</option>
            <option value="PREVENTIVE">PREVENTIVE</option>
          </select>
        </label>
        <label className="field">Priority
          <select className="input" value={form.priority} onChange={update('priority')}>
            <option value="LOW">LOW</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="HIGH">HIGH</option>
            <option value="URGENT">URGENT</option>
          </select>
        </label>
        <label className="field">Title
          <input className="input" value={form.title} onChange={update('title')} />
          {errors.title ? <span className="error-text">{errors.title}</span> : null}
        </label>
        <label className="field">Asset
          <input className="input" value={form.asset_id} onChange={update('asset_id')} />
        </label>
        <label className="field">Room
          <input className="input" value={form.room_id} onChange={update('room_id')} />
        </label>
        <label className="field">Property
          <input className="input" value={form.property_id} onChange={update('property_id')} />
        </label>
        <label className="field">Department
          <input className="input" value={form.department_id} onChange={update('department_id')} />
        </label>
        <label className="field">Assigned To
          <input className="input" value={form.assigned_to} onChange={update('assigned_to')} />
        </label>
        <label className="field">Scheduled At
          <input className="input" type="datetime-local" value={form.scheduled_at} onChange={update('scheduled_at')} />
        </label>
        <label className="field">Due At
          <input className="input" type="datetime-local" value={form.due_at} onChange={update('due_at')} />
          {errors.due_at ? <span className="error-text">{errors.due_at}</span> : null}
        </label>
      </div>
      <label className="field">Description
        <textarea className="input" rows={3} value={form.description} onChange={update('description')} />
      </label>
      <button className="button" type="submit" disabled={saving}>{saving ? 'Saving...' : mode === 'create' ? 'Create Task' : 'Update Task'}</button>
    </form>
  )
}
