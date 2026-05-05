import { useState } from 'react'
import { useAuth } from '../../../features/auth/authContext'
import { createPMSchedule, runPMScheduler } from '../api/maintenance.api'
import { usePMSchedules } from '../hooks/useMaintenance'

export function PMSchedulesPage() {
  const { auth } = useAuth()
  const [form, setForm] = useState({ asset_id: '', title: '', frequency_type: 'MONTHLY', frequency_interval: '1', next_run_at: '', start_date: '', end_date: '', priority: 'MEDIUM', is_active: true })
  const [saving, setSaving] = useState(false)
  const { data, loading, error, reload } = usePMSchedules(auth?.accessToken, auth?.user?.org_id, 1, 50)

  const create = async () => {
    if (!auth?.accessToken || !auth.user?.org_id) return
    setSaving(true)
    try {
      await createPMSchedule(auth.accessToken, { org_id: auth.user.org_id, asset_id: Number(form.asset_id), title: form.title, description: '', frequency_type: form.frequency_type, frequency_interval: Number(form.frequency_interval), next_run_at: new Date(form.next_run_at).toISOString(), start_date: form.start_date, end_date: form.end_date || null, priority: form.priority, is_active: form.is_active })
      await reload()
    } finally {
      setSaving(false)
    }
  }

  return <div className="page full"><div className="glass panel"><h2>PM Schedules</h2>
    <div className="grid-form three">
      <input className="input" placeholder="Asset ID" value={form.asset_id} onChange={(e) => setForm((p) => ({ ...p, asset_id: e.target.value }))} />
      <input className="input" placeholder="Title" value={form.title} onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))} />
      <select className="input" value={form.frequency_type} onChange={(e) => setForm((p) => ({ ...p, frequency_type: e.target.value }))}><option>DAILY</option><option>WEEKLY</option><option>MONTHLY</option><option>QUARTERLY</option><option>YEARLY</option><option>CUSTOM</option></select>
      <input className="input" type="number" min={1} value={form.frequency_interval} onChange={(e) => setForm((p) => ({ ...p, frequency_interval: e.target.value }))} />
      <input className="input" type="datetime-local" value={form.next_run_at} onChange={(e) => setForm((p) => ({ ...p, next_run_at: e.target.value }))} />
      <input className="input" type="date" value={form.start_date} onChange={(e) => setForm((p) => ({ ...p, start_date: e.target.value }))} />
    </div>
    <button className="button" onClick={create} disabled={saving}>{saving ? 'Saving...' : 'Create PM Schedule'}</button>
    <button className="button secondary" onClick={async () => { if (!auth?.accessToken || !auth.user?.org_id) return; await runPMScheduler(auth.accessToken, { org_id: auth.user.org_id }); await reload() }}>Run Scheduler</button>
    {loading ? <p>Loading...</p> : null}{error ? <p className="error-text">{error}</p> : null}
    <ul className="simple-list">{(data?.results || []).map((schedule) => <li key={schedule.id}>{schedule.title} • {schedule.frequency_type} • next {new Date(schedule.next_run_at).toLocaleString()} • {schedule.is_active ? 'ACTIVE' : 'INACTIVE'}</li>)}</ul>
  </div></div>
}
