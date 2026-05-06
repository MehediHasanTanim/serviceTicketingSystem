import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { ProjectBoard } from '../components/ProjectBoard'
import { useProjects } from '../hooks/useProjects'
import type { ProjectListFilters } from '../types/projects.types'

const base: ProjectListFilters = { q: '', property: '', department: '', project_type: '', status: '', priority: '', owner: '', manager: '', date_from: '', date_to: '', page: 1, page_size: 10, sort_by: 'updated_at', sort_dir: 'desc' }

export function ProjectsPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const [view, setView] = useState<'table' | 'board'>((params.get('view') as any) || 'table')
  const [filters, setFilters] = useState<ProjectListFilters>({ ...base, ...Object.fromEntries(params.entries()), page: Number(params.get('page') || '1'), page_size: Number(params.get('page_size') || '10') })
  const { data, loading, error, reload } = useProjects(auth?.accessToken, auth?.user?.org_id, filters)

  useEffect(() => {
    const p = new URLSearchParams()
    Object.entries(filters).forEach(([k, v]) => { if (String(v)) p.set(k, String(v)) })
    p.set('view', view)
    setParams(p, { replace: true })
  }, [filters, view, setParams])

  const pages = Math.max(1, Math.ceil((data?.count || 0) / filters.page_size))

  return <div className="page full"><div className="glass panel">
    <div className="section-head"><h2>Projects</h2><div className="inline-actions"><button className="button secondary small" onClick={() => setView(view === 'table' ? 'board' : 'table')}>View: {view}</button><button className="button" onClick={() => navigate('/projects/new')}>New Project</button></div></div>
    <div className="grid-form filters-grid">
      <input className="input" placeholder="Search code/title" value={filters.q} onChange={(e) => setFilters((p) => ({ ...p, q: e.target.value, page: 1 }))} />
      <input className="input" placeholder="Property" value={filters.property} onChange={(e) => setFilters((p) => ({ ...p, property: e.target.value, page: 1 }))} />
      <input className="input" placeholder="Department" value={filters.department} onChange={(e) => setFilters((p) => ({ ...p, department: e.target.value, page: 1 }))} />
      <select className="input" value={filters.status} onChange={(e) => setFilters((p) => ({ ...p, status: e.target.value, page: 1 }))}><option value="">All status</option>{['DRAFT', 'PLANNED', 'IN_PROGRESS', 'ON_HOLD', 'COMPLETED', 'CANCELLED', 'VOID'].map((x) => <option key={x} value={x}>{x}</option>)}</select>
      <select className="input" value={filters.priority} onChange={(e) => setFilters((p) => ({ ...p, priority: e.target.value, page: 1 }))}><option value="">All priority</option>{['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((x) => <option key={x} value={x}>{x}</option>)}</select>
      <input className="input" type="date" value={filters.date_from} onChange={(e) => setFilters((p) => ({ ...p, date_from: e.target.value, page: 1 }))} />
      <input className="input" type="date" value={filters.date_to} onChange={(e) => setFilters((p) => ({ ...p, date_to: e.target.value, page: 1 }))} />
    </div>
    <ProjectBoard view={view} projects={data?.results || []} loading={loading} error={error} onRetry={reload} onRowClick={(id) => navigate(`/projects/${id}`)} />
    <div className="pagination-row"><button className="button secondary small" disabled={filters.page <= 1} onClick={() => setFilters((p) => ({ ...p, page: p.page - 1 }))}>Prev</button><span>Page {filters.page} of {pages}</span><button className="button secondary small" disabled={filters.page >= pages} onClick={() => setFilters((p) => ({ ...p, page: p.page + 1 }))}>Next</button></div>
  </div></div>
}
