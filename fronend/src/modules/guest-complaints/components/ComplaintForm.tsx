import { useState } from 'react'
import type { ComplaintCategory, ComplaintSeverity, ComplaintSource, GuestComplaint } from '../types/guestComplaints.types'

type Props = {
  orgId: number
  mode: 'create' | 'edit'
  initial?: GuestComplaint
  onSubmit: (payload: Record<string, unknown>) => Promise<void> | void
  saving?: boolean
  apiError?: string
}

const categories: ComplaintCategory[] = ['ROOM_CLEANLINESS', 'MAINTENANCE', 'NOISE', 'STAFF_BEHAVIOR', 'BILLING', 'FOOD_BEVERAGE', 'CHECK_IN_CHECK_OUT', 'SAFETY_SECURITY', 'OTHER']
const severities: ComplaintSeverity[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
const sources: ComplaintSource[] = ['FRONT_DESK', 'GUEST_PORTAL', 'PHONE', 'EMAIL', 'STAFF', 'PMS', 'OTHER']

export function ComplaintForm({ orgId, mode, initial, onSubmit, saving, apiError }: Props) {
  const [form, setForm] = useState({
    guest_id: initial?.guest_id ? String(initial.guest_id) : '',
    guest_name: initial?.guest_name || '',
    guest_contact: initial?.guest_contact || '',
    property_id: initial?.property_id ? String(initial.property_id) : '',
    room_id: initial?.room_id ? String(initial.room_id) : '',
    department_id: initial?.department_id ? String(initial.department_id) : '',
    category: (initial?.category || 'OTHER') as ComplaintCategory,
    severity: (initial?.severity || 'MEDIUM') as ComplaintSeverity,
    source: (initial?.source || 'FRONT_DESK') as ComplaintSource,
    title: initial?.title || '',
    description: initial?.description || '',
    assigned_to: initial?.assigned_to ? String(initial.assigned_to) : '',
    due_at: initial?.due_at ? initial.due_at.slice(0, 16) : '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const update = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => setForm((p) => ({ ...p, [key]: e.target.value }))

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    const next: Record<string, string> = {}
    if (!form.guest_name.trim()) next.guest_name = 'Guest name is required.'
    if (!form.property_id.trim()) next.property_id = 'Property is required.'
    if (!form.title.trim()) next.title = 'Title is required.'
    if (!form.category) next.category = 'Category is required.'
    if (!form.severity) next.severity = 'Severity is required.'
    if (!form.source) next.source = 'Source is required.'
    setErrors(next)
    if (Object.keys(next).length) return

    await onSubmit({
      org_id: orgId,
      guest_id: form.guest_id ? Number(form.guest_id) : null,
      guest_name: form.guest_name.trim(),
      guest_contact: form.guest_contact.trim(),
      property_id: Number(form.property_id),
      room_id: form.room_id ? Number(form.room_id) : null,
      department_id: form.department_id ? Number(form.department_id) : null,
      category: form.category,
      severity: form.severity,
      source: form.source,
      title: form.title.trim(),
      description: form.description.trim(),
      assigned_to: form.assigned_to ? Number(form.assigned_to) : null,
      due_at: form.due_at ? new Date(form.due_at).toISOString() : null,
    })
  }

  return (
    <form className="card-section" onSubmit={submit} aria-label="Complaint Form">
      <h3>{mode === 'create' ? 'New Complaint' : 'Edit Complaint'}</h3>
      {apiError ? <p className="error-text">{apiError}</p> : null}
      <div className="grid-form two">
        <label className="field">Guest Name<input className="input" value={form.guest_name} onChange={update('guest_name')} />{errors.guest_name ? <span className="error-text">{errors.guest_name}</span> : null}</label>
        <label className="field">Guest ID<input className="input" value={form.guest_id} onChange={update('guest_id')} /></label>
        <label className="field">Guest Contact<input className="input" value={form.guest_contact} onChange={update('guest_contact')} /></label>
        <label className="field">Property ID<input className="input" value={form.property_id} onChange={update('property_id')} />{errors.property_id ? <span className="error-text">{errors.property_id}</span> : null}</label>
        <label className="field">Room ID<input className="input" value={form.room_id} onChange={update('room_id')} /></label>
        <label className="field">Department ID<input className="input" value={form.department_id} onChange={update('department_id')} /></label>
        <label className="field">Category<select className="input" value={form.category} onChange={update('category')}>{categories.map((v) => <option key={v} value={v}>{v}</option>)}</select></label>
        <label className="field">Severity<select className="input" value={form.severity} onChange={update('severity')}>{severities.map((v) => <option key={v} value={v}>{v}</option>)}</select></label>
        <label className="field">Source<select className="input" value={form.source} onChange={update('source')}>{sources.map((v) => <option key={v} value={v}>{v}</option>)}</select></label>
        <label className="field">Assigned To<input className="input" value={form.assigned_to} onChange={update('assigned_to')} /></label>
        <label className="field">Due At<input className="input" type="datetime-local" value={form.due_at} onChange={update('due_at')} /></label>
        <label className="field">Title<input className="input" value={form.title} onChange={update('title')} />{errors.title ? <span className="error-text">{errors.title}</span> : null}</label>
      </div>
      <label className="field">Description<textarea className="input" rows={4} value={form.description} onChange={update('description')} /></label>
      <button className="button" type="submit" disabled={saving}>{saving ? 'Saving...' : mode === 'create' ? 'Create' : 'Update'}</button>
    </form>
  )
}
