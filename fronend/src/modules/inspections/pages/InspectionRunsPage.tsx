import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useCreateInspectionRun, useInspectionRuns, useInspectionTemplates, useStartInspectionRun } from '../hooks/useInspections'
import type { InspectionRunFilters } from '../types/inspections.types'

const base: InspectionRunFilters = { template_id: '', status: '', result: '', property: '', department: '', location: '', room: '', asset: '', assigned_to: '', inspected_by: '', page: 1, page_size: 10 }

export function InspectionRunsPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const [filters, setFilters] = useState(base)
  const [form, setForm] = useState({ template_id: '', property_id: '', department_id: '', location_id: '', room_id: '', asset_id: '', assigned_to: '', notes: '' })
  const { data, loading, error, reload } = useInspectionRuns(auth?.accessToken, auth?.user?.org_id, filters)
  const templates = useInspectionTemplates(auth?.accessToken, auth?.user?.org_id, { q: '', category: '', department: '', property: '', is_active: 'true', page: 1, page_size: 100 })
  const createRun = useCreateInspectionRun()
  const startRun = useStartInspectionRun()

  const create = async () => {
    if (!auth?.accessToken || !auth.user?.org_id || !form.template_id) return
    await createRun(auth.accessToken, { org_id: auth.user.org_id, template_id: Number(form.template_id), property_id: form.property_id ? Number(form.property_id) : null, department_id: form.department_id ? Number(form.department_id) : null, location_id: form.location_id ? Number(form.location_id) : null, room_id: form.room_id ? Number(form.room_id) : null, asset_id: form.asset_id ? Number(form.asset_id) : null, assigned_to: form.assigned_to ? Number(form.assigned_to) : null, notes: form.notes })
    reload()
  }

  return <div className="page full"><div className="glass panel">
    <h2>Inspection Runs</h2>
    <div className="card-section">
      <h3>Create Inspection Run</h3>
      <div className="grid-form three"><select className="input" value={form.template_id} onChange={(e) => setForm((p) => ({ ...p, template_id: e.target.value }))}><option value="">Select active template</option>{(templates.data?.results || []).filter((t) => t.is_active).map((t) => <option key={t.id} value={t.id}>{t.template_code} - {t.name}</option>)}</select><input className="input" placeholder="Property ID" value={form.property_id} onChange={(e) => setForm((p) => ({ ...p, property_id: e.target.value }))} /><input className="input" placeholder="Department ID" value={form.department_id} onChange={(e) => setForm((p) => ({ ...p, department_id: e.target.value }))} /></div>
      <textarea className="input" placeholder="Notes" value={form.notes} onChange={(e) => setForm((p) => ({ ...p, notes: e.target.value }))} />
      <button className="button" onClick={create}>Create Run</button>
    </div>
    <div className="grid-form three"><input className="input" placeholder="Template ID" value={filters.template_id} onChange={(e) => setFilters((p) => ({ ...p, template_id: e.target.value }))} /><input className="input" placeholder="Status" value={filters.status} onChange={(e) => setFilters((p) => ({ ...p, status: e.target.value }))} /><input className="input" placeholder="Result" value={filters.result} onChange={(e) => setFilters((p) => ({ ...p, result: e.target.value }))} /></div>
    {loading ? <p>Loading runs...</p> : null}{error ? <p className="error-text">{error}</p> : null}
    <div className="table-wrap"><table className="data-table"><thead><tr><th>Inspection Number</th><th>Template</th><th>Property</th><th>Location/Room/Asset</th><th>Assigned To</th><th>Inspected By</th><th>Status</th><th>Result</th><th>Final Score</th><th>Created At</th><th>Actions</th></tr></thead><tbody>
      {(data?.results || []).map((row) => <tr key={row.id}><td>{row.inspection_number}</td><td>{row.template_id}</td><td>{row.property_id || '-'}</td><td>{[row.location_id, row.room_id, row.asset_id].filter(Boolean).join(' / ') || '-'}</td><td>{row.assigned_to || '-'}</td><td>{row.inspected_by || '-'}</td><td>{row.status}</td><td>{row.result || '-'}</td><td>{row.final_score || '-'}</td><td>{new Date(row.created_at).toLocaleString()}</td><td><button className="button secondary small" onClick={() => navigate(`/inspections/runs/${row.id}`)}>Open</button> <button className="button secondary small" disabled={row.status !== 'PENDING'} onClick={async () => { if (!auth?.accessToken || !auth.user?.org_id) return; await startRun(auth.accessToken, row.id, { org_id: auth.user.org_id }); reload() }}>Start</button> <button className="button secondary small" onClick={() => navigate(`/inspections/runs/${row.id}/execute`)}>Execute</button></td></tr>)}
    </tbody></table></div>
  </div></div>
}
