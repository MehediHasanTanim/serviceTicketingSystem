import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useActivateInspectionTemplate, useDeactivateInspectionTemplate, useInspectionTemplates } from '../hooks/useInspections'
import type { InspectionTemplateFilters } from '../types/inspections.types'

const base: InspectionTemplateFilters = { q: '', category: '', department: '', property: '', is_active: '', page: 1, page_size: 10 }

export function InspectionTemplatesPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const [filters, setFilters] = useState(base)
  const { data, loading, error, reload } = useInspectionTemplates(auth?.accessToken, auth?.user?.org_id, filters)
  const activate = useActivateInspectionTemplate()
  const deactivate = useDeactivateInspectionTemplate()

  const toggle = async (id: number, active: boolean) => {
    if (!auth?.accessToken || !auth.user?.org_id) return
    if (active) await deactivate(auth.accessToken, id, { org_id: auth.user.org_id })
    else await activate(auth.accessToken, id, { org_id: auth.user.org_id })
    reload()
  }

  return <div className="page full"><div className="glass panel">
    <div className="section-head"><h2>Inspection Templates</h2><button className="button" onClick={() => navigate('/inspections/templates/new')}>New Template</button></div>
    <div className="grid-form three"><input className="input" placeholder="Search code/name" value={filters.q} onChange={(e) => setFilters((p) => ({ ...p, q: e.target.value }))} /><input className="input" placeholder="Category" value={filters.category} onChange={(e) => setFilters((p) => ({ ...p, category: e.target.value }))} /><select className="input" value={filters.is_active} onChange={(e) => setFilters((p) => ({ ...p, is_active: e.target.value }))}><option value="">All status</option><option value="true">Active</option><option value="false">Inactive</option></select></div>
    {loading ? <p>Loading templates...</p> : null}
    {error ? <p className="error-text">{error}</p> : null}
    <div className="table-wrap"><table className="data-table"><thead><tr><th>Template Code</th><th>Name</th><th>Category</th><th>Department</th><th>Property</th><th>Version</th><th>Status</th><th>Updated</th><th>Actions</th></tr></thead><tbody>
      {(data?.results || []).slice((filters.page - 1) * filters.page_size, filters.page * filters.page_size).map((row) => <tr key={row.id} onClick={() => navigate(`/inspections/templates/${row.id}`)}><td>{row.template_code}</td><td>{row.name}</td><td>{row.category || '-'}</td><td>{row.department_id || '-'}</td><td>{row.property_id || '-'}</td><td>{row.version}</td><td>{row.is_active ? 'Active' : 'Inactive'}</td><td>{new Date(row.updated_at).toLocaleString()}</td><td><button className="button secondary small" onClick={(e) => { e.stopPropagation(); navigate(`/inspections/templates/${row.id}/edit`) }}>Edit</button> <button className="button secondary small" onClick={(e) => { e.stopPropagation(); toggle(row.id, row.is_active) }}>{row.is_active ? 'Deactivate' : 'Activate'}</button></td></tr>)}
    </tbody></table></div>
  </div></div>
}
