import { useMemo, useState } from 'react'
import type { ServiceOrder, ServiceOrderPriority, ServiceOrderType } from '../types'

type Props = {
  orgId: number
  mode: 'create' | 'edit'
  initial?: ServiceOrder
  users: Array<{ id: number; label: string }>
  onSubmit: (payload: Record<string, unknown>) => Promise<void> | void
  saving?: boolean
}

type FormState = {
  title: string
  description: string
  customer_id: string
  asset_id: string
  priority: ServiceOrderPriority
  type: ServiceOrderType
  due_date: string
  scheduled_at: string
  assigned_to: string
}

const baseForm: FormState = {
  title: '',
  description: '',
  customer_id: '',
  asset_id: '',
  priority: 'MEDIUM',
  type: 'OTHER',
  due_date: '',
  scheduled_at: '',
  assigned_to: '',
}

export function OrderForm({ orgId, mode, initial, users, onSubmit, saving }: Props) {
  const [form, setForm] = useState<FormState>(() => {
    if (!initial) return baseForm
    return {
      title: initial.title,
      description: initial.description,
      customer_id: String(initial.customer_id),
      asset_id: initial.asset_id ? String(initial.asset_id) : '',
      priority: initial.priority,
      type: initial.type,
      due_date: initial.due_date || '',
      scheduled_at: initial.scheduled_at ? initial.scheduled_at.slice(0, 16) : '',
      assigned_to: initial.assigned_to ? String(initial.assigned_to) : '',
    }
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const heading = useMemo(() => (mode === 'create' ? 'Create Service Order' : 'Edit Service Order'), [mode])

  const update = (key: keyof FormState) => (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setForm((prev) => ({ ...prev, [key]: event.target.value }))
  }

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    const nextErrors: Record<string, string> = {}
    if (!form.title.trim()) nextErrors.title = 'Title is required.'
    if (!form.customer_id.trim()) nextErrors.customer_id = 'Customer is required.'
    if (form.customer_id && Number.isNaN(Number(form.customer_id))) nextErrors.customer_id = 'Customer must be a number.'
    if (form.asset_id && Number.isNaN(Number(form.asset_id))) nextErrors.asset_id = 'Asset must be a number.'
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length) return

    await onSubmit({
      org_id: orgId,
      title: form.title.trim(),
      description: form.description.trim(),
      customer_id: Number(form.customer_id),
      asset_id: form.asset_id ? Number(form.asset_id) : null,
      priority: form.priority,
      type: form.type,
      due_date: form.due_date || null,
      scheduled_at: form.scheduled_at ? new Date(form.scheduled_at).toISOString() : null,
      assigned_to: form.assigned_to ? Number(form.assigned_to) : null,
    })
  }

  return (
    <form onSubmit={submit} className="card-section" aria-label={heading}>
      <h3>{heading}</h3>
      <div className="grid-form two">
        <label className="field" htmlFor="order-title">Title
          <input id="order-title" className="input" value={form.title} onChange={update('title')} />
          {errors.title ? <span className="error-text">{errors.title}</span> : null}
        </label>
        <label className="field" htmlFor="order-customer">Customer
          <input id="order-customer" className="input" value={form.customer_id} onChange={update('customer_id')} />
          {errors.customer_id ? <span className="error-text">{errors.customer_id}</span> : null}
        </label>
        <label className="field" htmlFor="order-priority">Priority
          <select id="order-priority" className="input" value={form.priority} onChange={update('priority')}>
            <option value="LOW">LOW</option><option value="MEDIUM">MEDIUM</option><option value="HIGH">HIGH</option><option value="URGENT">URGENT</option>
          </select>
        </label>
        <label className="field" htmlFor="order-type">Type
          <select id="order-type" className="input" value={form.type} onChange={update('type')}>
            <option value="INSTALLATION">INSTALLATION</option><option value="REPAIR">REPAIR</option><option value="MAINTENANCE">MAINTENANCE</option><option value="INSPECTION">INSPECTION</option><option value="OTHER">OTHER</option>
          </select>
        </label>
        <label className="field" htmlFor="order-asset">Asset (optional)
          <input id="order-asset" className="input" value={form.asset_id} onChange={update('asset_id')} />
          {errors.asset_id ? <span className="error-text">{errors.asset_id}</span> : null}
        </label>
        <label className="field" htmlFor="order-assignee">Assignee (optional)
          <select id="order-assignee" className="input" value={form.assigned_to} onChange={update('assigned_to')}>
            <option value="">Unassigned</option>
            {users.map((u) => <option key={u.id} value={u.id}>{u.label}</option>)}
          </select>
        </label>
        <label className="field" htmlFor="order-due-date">Due date
          <input id="order-due-date" type="date" className="input" value={form.due_date} onChange={update('due_date')} />
        </label>
        <label className="field" htmlFor="order-scheduled">Scheduled at
          <input id="order-scheduled" type="datetime-local" className="input" value={form.scheduled_at} onChange={update('scheduled_at')} />
        </label>
      </div>
      <label className="field" htmlFor="order-description">Description
        <textarea id="order-description" className="input" rows={4} value={form.description} onChange={update('description')} />
      </label>
      <button className="button" type="submit" disabled={saving}>{saving ? 'Saving...' : mode === 'create' ? 'Create' : 'Update'}</button>
    </form>
  )
}
