import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useBreakfastCountDetail, useCreateBreakfastCount, useUpdateBreakfastCount } from '../hooks/useFoodBeverage'

export function BreakfastCountFormPage() {
  const { id } = useParams(); const editing = !!id; const { auth } = useAuth(); const navigate = useNavigate()
  const detail = useBreakfastCountDetail(auth?.accessToken, auth?.user?.org_id, Number(id))
  const create = useCreateBreakfastCount(); const update = useUpdateBreakfastCount()
  const initial = detail.data
  const [form, setForm] = useState({ property_id: '', outlet_id: '', service_date: '', expected_guest_count: '0', actual_guest_count: '0', in_house_guest_count: '0', complimentary_count: '0', paid_count: '0', no_show_count: '0', notes: '' })
  const [busy, setBusy] = useState(false); const [error, setError] = useState('')

  const source = editing && initial ? { property_id: String(initial.property_id || ''), outlet_id: String(initial.outlet_id || ''), service_date: initial.service_date || '', expected_guest_count: String(initial.expected_guest_count || 0), actual_guest_count: String(initial.actual_guest_count || 0), in_house_guest_count: String(initial.in_house_guest_count || 0), complimentary_count: String(initial.complimentary_count || 0), paid_count: String(initial.paid_count || 0), no_show_count: String(initial.no_show_count || 0), notes: initial.notes || '' } : form
  const sync = (key: keyof typeof source, value: string) => setForm((p) => ({ ...p, [key]: value }))

  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); if (!auth?.accessToken || !auth?.user?.org_id) return
    const counts = ['expected_guest_count', 'actual_guest_count', 'in_house_guest_count', 'complimentary_count', 'paid_count', 'no_show_count'] as const
    for (const k of counts) if (Number(source[k]) < 0) return setError('All count fields must be non-negative.')
    if (!source.service_date || !source.property_id || !source.outlet_id) return setError('Service date, property, and outlet are required.')
    if (Number(source.actual_guest_count) !== Number(source.complimentary_count) + Number(source.paid_count)) return setError('Actual guests should match complimentary + paid counts.')
    setBusy(true); setError('')
    try {
      const payload = { org_id: auth.user.org_id, property_id: Number(source.property_id), outlet_id: Number(source.outlet_id), service_date: source.service_date, expected_guest_count: Number(source.expected_guest_count), actual_guest_count: Number(source.actual_guest_count), in_house_guest_count: Number(source.in_house_guest_count), complimentary_count: Number(source.complimentary_count), paid_count: Number(source.paid_count), no_show_count: Number(source.no_show_count), notes: source.notes.trim() || null }
      if (editing) await update(auth.accessToken, Number(id), payload); else await create(auth.accessToken, payload)
      navigate('/food-beverage/breakfast-counts')
    } catch (err: any) { setError(err?.details?.detail || err.message || 'Failed to save breakfast count.') } finally { setBusy(false) }
  }

  return <div className="page full"><div className="glass panel"><h2>{editing ? 'Edit' : 'Create'} Breakfast Count</h2>
    <form className="card-section" onSubmit={submit}><div className="grid-form two">
      <label className="field">Property<input className="input" value={source.property_id} onChange={(e) => sync('property_id', e.target.value)} /></label>
      <label className="field">Outlet<input className="input" value={source.outlet_id} onChange={(e) => sync('outlet_id', e.target.value)} /></label>
      <label className="field">Service Date<input className="input" type="date" value={source.service_date} onChange={(e) => sync('service_date', e.target.value)} /></label>
      <label className="field">Expected Guests<input className="input" type="number" value={source.expected_guest_count} onChange={(e) => sync('expected_guest_count', e.target.value)} /></label>
      <label className="field">Actual Guests<input className="input" type="number" value={source.actual_guest_count} onChange={(e) => sync('actual_guest_count', e.target.value)} /></label>
      <label className="field">In-house Guests<input className="input" type="number" value={source.in_house_guest_count} onChange={(e) => sync('in_house_guest_count', e.target.value)} /></label>
      <label className="field">Complimentary<input className="input" type="number" value={source.complimentary_count} onChange={(e) => sync('complimentary_count', e.target.value)} /></label>
      <label className="field">Paid<input className="input" type="number" value={source.paid_count} onChange={(e) => sync('paid_count', e.target.value)} /></label>
      <label className="field">No-show<input className="input" type="number" value={source.no_show_count} onChange={(e) => sync('no_show_count', e.target.value)} /></label>
    </div>
    <label className="field">Notes<textarea className="input" rows={3} value={source.notes} onChange={(e) => sync('notes', e.target.value)} /></label>
    {error ? <p className="error-text">{error}</p> : null}
    <button className="button" disabled={busy} type="submit">{busy ? 'Saving...' : 'Save'}</button></form>
  </div></div>
}
