import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { AuditLogs } from '../components/AuditLogs'
import { SnaggingForm, TechnicalAuditForm } from '../components/Forms'
import { ProjectTimeline } from '../components/ProjectTimeline'
import { SnaggingItems } from '../components/SnaggingItems'
import { TechnicalAudits } from '../components/TechnicalAudits'
import { useCreateSnaggingItem, useCreateTechnicalAudit, useProjectAuditLogs, useProjectDetail, useProjectSnaggingItems, useProjectTimeline, useSnaggingItemAction, useTechnicalAuditAction, useTechnicalAudits, useUpdateProjectProgress, useUpdateProjectStatus } from '../hooks/useProjects'
import { priorityClass } from '../components/utils'

export function ProjectDetailPage() {
  const { id } = useParams()
  const projectId = Number(id)
  const navigate = useNavigate()
  const { auth } = useAuth()
  const [tab, setTab] = useState<'overview' | 'timeline' | 'snag' | 'audit' | 'logs'>('overview')
  const [busy, setBusy] = useState(false)
  const [snagFilters, setSnagFilters] = useState({ q: '', category: '', severity: '', status: '', assigned_to: '', room: '', location: '', due_from: '', due_to: '', page: 1, page_size: 10, sort_by: 'created_at', sort_dir: 'desc' as const })
  const [auditFilters, setAuditFilters] = useState({ q: '', status: '', result: '', auditor: '', conducted_from: '', conducted_to: '', page: 1, page_size: 10, sort_by: 'created_at', sort_dir: 'desc' as const })

  const detail = useProjectDetail(auth?.accessToken, auth?.user?.org_id, projectId)
  const timeline = useProjectTimeline(auth?.accessToken, auth?.user?.org_id, projectId)
  const snagging = useProjectSnaggingItems(auth?.accessToken, auth?.user?.org_id, projectId, snagFilters)
  const audits = useTechnicalAudits(auth?.accessToken, auth?.user?.org_id, projectId, auditFilters)
  const logs = useProjectAuditLogs(auth?.accessToken, auth?.user?.org_id, { q: '', property_id: '', actor_user_id: '', action: '', target_type: '', target_id: String(projectId), date_from: '', date_to: '', page: 1, page_size: 20, sort_by: 'created_at', sort_dir: 'desc' })

  const updateStatus = useUpdateProjectStatus()
  const updateProgress = useUpdateProjectProgress()
  const createSnag = useCreateSnaggingItem()
  const createAudit = useCreateTechnicalAudit()
  const snagAction = useSnaggingItemAction()
  const auditAction = useTechnicalAuditAction()

  const refreshAll = async () => Promise.all([detail.reload(), timeline.reload(), snagging.reload(), audits.reload(), logs.reload()])
  const project = detail.data

  if (detail.loading) return <div className="page full"><div className="glass panel"><p>Loading project...</p></div></div>
  if (!project) return <div className="page full"><div className="glass panel"><p className="error-text">{detail.error || 'Project not found'}</p></div></div>

  return <div className="page full"><div className="glass panel">
    <div className="section-head"><div><h2>{project.project_code} • {project.title}</h2><div className="badge-row"><span className="badge neutral">{project.project_type}</span><span className="badge neutral">{project.status}</span><span className={`badge ${priorityClass(project.priority)}`}>{project.priority}</span></div></div>
      <div className="inline-actions"><button className="button secondary small" onClick={() => navigate(`/projects/${project.id}/edit`)}>Edit</button><button className="button secondary small" onClick={() => navigate('/projects/audit-logs')}>Audit Logs</button></div>
    </div>

    <div className="card-section sticky-summary"><div className="grid-form three"><div><strong>Owner:</strong> {project.owner_id || '-'}</div><div><strong>Manager:</strong> {project.manager_id || '-'}</div><div><strong>Progress:</strong> <progress max={100} value={project.progress_percentage} /> {project.progress_percentage}%</div><div><strong>Planned end:</strong> {project.planned_end_date || '-'}</div><div><strong>Actual end:</strong> {project.actual_end_date || '-'}</div></div>
      <div className="inline-actions"><button className="button secondary small" disabled={busy} onClick={async () => {
        if (!auth?.accessToken || !auth.user?.org_id) return
        const next = prompt('New progress (0-100)')
        if (!next) return
        const n = Number(next)
        if (n < 0 || n > 100) return
        setBusy(true)
        try { await updateProgress(auth.accessToken, project.id, { org_id: auth.user.org_id, progress_percentage: n, message: '' }); await refreshAll() } finally { setBusy(false) }
      }}>Update Progress</button>
        <button className="button secondary small" disabled={busy} onClick={async () => {
          if (!auth?.accessToken || !auth.user?.org_id) return
          const newStatus = prompt('New status (DRAFT|PLANNED|IN_PROGRESS|ON_HOLD|COMPLETED|CANCELLED|VOID)')
          if (!newStatus) return
          let actualEndDate: string | null = null
          if (newStatus === 'COMPLETED') actualEndDate = prompt('Actual end date YYYY-MM-DD') || null
          if (['COMPLETED', 'CANCELLED', 'VOID'].includes(newStatus) && !window.confirm(`Confirm ${newStatus}?`)) return
          setBusy(true)
          try { await updateStatus(auth.accessToken, project.id, { org_id: auth.user.org_id, new_status: newStatus, message: '', actual_end_date: actualEndDate }); await refreshAll() } finally { setBusy(false) }
        }}>Update Status</button></div>
    </div>

    <div className="tabs-row">{[['overview', 'Overview'], ['timeline', 'Progress & Timeline'], ['snag', 'Snagging Items'], ['audit', 'Technical Audits'], ['logs', 'Audit Logs']].map(([key, label]) => <button key={key} className={`tab ${tab === key ? 'active' : ''}`} onClick={() => setTab(key as any)}>{label}</button>)}</div>

    {tab === 'overview' ? <div className="card-section"><p>{project.description || 'No description.'}</p></div> : null}
    {tab === 'timeline' ? <ProjectTimeline events={timeline.data?.results || []} loading={timeline.loading} error={timeline.error} /> : null}
    {tab === 'snag' ? <><SnaggingForm orgId={auth?.user?.org_id || 0} saving={busy} onSubmit={async (payload) => { if (!auth?.accessToken) return; setBusy(true); try { await createSnag(auth.accessToken, project.id, payload); await refreshAll() } finally { setBusy(false) } }} />
      <div className="grid-form three">
        <input className="input" placeholder="Search snag #/title" value={snagFilters.q} onChange={(e) => setSnagFilters((p) => ({ ...p, q: e.target.value, page: 1 }))} />
        <select className="input" value={snagFilters.severity} onChange={(e) => setSnagFilters((p) => ({ ...p, severity: e.target.value, page: 1 }))}><option value="">All severity</option>{['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((x) => <option key={x} value={x}>{x}</option>)}</select>
        <select className="input" value={snagFilters.status} onChange={(e) => setSnagFilters((p) => ({ ...p, status: e.target.value, page: 1 }))}><option value="">All status</option>{['OPEN', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'VERIFIED', 'REOPENED', 'CANCELLED', 'VOID'].map((x) => <option key={x} value={x}>{x}</option>)}</select>
      </div>
      <SnaggingItems items={snagging.data?.results || []} onOpen={(snagId) => navigate(`/projects/snagging-items/${snagId}`)} busy={busy} onAction={async (snagId, action, payload) => { if (!auth?.accessToken || !auth.user?.org_id) return; setBusy(true); try { await snagAction(auth.accessToken, snagId, action, { org_id: auth.user.org_id, ...payload }); await refreshAll() } finally { setBusy(false) } }} />
      <div className="pagination-row"><button className="button secondary small" disabled={snagFilters.page <= 1} onClick={() => setSnagFilters((p) => ({ ...p, page: p.page - 1 }))}>Prev</button><span>Page {snagFilters.page} of {Math.max(1, Math.ceil((snagging.data?.count || 0) / snagFilters.page_size))}</span><button className="button secondary small" disabled={snagFilters.page >= Math.max(1, Math.ceil((snagging.data?.count || 0) / snagFilters.page_size))} onClick={() => setSnagFilters((p) => ({ ...p, page: p.page + 1 }))}>Next</button></div>
    </> : null}
    {tab === 'audit' ? <><TechnicalAuditForm orgId={auth?.user?.org_id || 0} saving={busy} onSubmit={async (payload) => { if (!auth?.accessToken) return; setBusy(true); try { await createAudit(auth.accessToken, project.id, payload); await refreshAll() } finally { setBusy(false) } }} />
      <div className="grid-form three">
        <input className="input" placeholder="Search audit #/title" value={auditFilters.q} onChange={(e) => setAuditFilters((p) => ({ ...p, q: e.target.value, page: 1 }))} />
        <select className="input" value={auditFilters.status} onChange={(e) => setAuditFilters((p) => ({ ...p, status: e.target.value, page: 1 }))}><option value="">All status</option>{['SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'VOID'].map((x) => <option key={x} value={x}>{x}</option>)}</select>
        <select className="input" value={auditFilters.result} onChange={(e) => setAuditFilters((p) => ({ ...p, result: e.target.value, page: 1 }))}><option value="">All result</option>{['PASS', 'FAIL', 'PARTIAL', 'OBSERVATION'].map((x) => <option key={x} value={x}>{x}</option>)}</select>
      </div>
      <TechnicalAudits items={audits.data?.results || []} onOpen={(auditId) => navigate(`/projects/technical-audits/${auditId}`)} busy={busy} onAction={async (auditId, action, payload) => { if (!auth?.accessToken || !auth.user?.org_id) return; setBusy(true); try { await auditAction(auth.accessToken, auditId, action, { org_id: auth.user.org_id, ...payload }); await refreshAll() } finally { setBusy(false) } }} />
      <div className="pagination-row"><button className="button secondary small" disabled={auditFilters.page <= 1} onClick={() => setAuditFilters((p) => ({ ...p, page: p.page - 1 }))}>Prev</button><span>Page {auditFilters.page} of {Math.max(1, Math.ceil((audits.data?.count || 0) / auditFilters.page_size))}</span><button className="button secondary small" disabled={auditFilters.page >= Math.max(1, Math.ceil((audits.data?.count || 0) / auditFilters.page_size))} onClick={() => setAuditFilters((p) => ({ ...p, page: p.page + 1 }))}>Next</button></div>
    </> : null}
    {tab === 'logs' ? <AuditLogs rows={logs.data?.results || []} /> : null}
  </div></div>
}
