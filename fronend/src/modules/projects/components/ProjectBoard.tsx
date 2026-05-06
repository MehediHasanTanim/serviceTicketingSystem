import type { Project, ProjectStatus } from '../types/projects.types'
import { isProjectOverdue, priorityClass } from './utils'

type Props = {
  view: 'table' | 'board'
  projects: Project[]
  loading: boolean
  error: string
  onRetry: () => void
  onRowClick: (id: number) => void
}

const boardStatuses: ProjectStatus[] = ['DRAFT', 'PLANNED', 'IN_PROGRESS', 'ON_HOLD', 'COMPLETED', 'CANCELLED', 'VOID']

export function ProjectBoard({ view, projects, loading, error, onRetry, onRowClick }: Props) {
  if (loading) return <p>Loading projects...</p>
  if (error) return <div><p className="error-text">{error}</p><button className="button secondary small" onClick={onRetry}>Retry</button></div>
  if (!projects.length) return <p className="hint">No projects found.</p>

  if (view === 'board') {
    return <div className="hk-board">{boardStatuses.map((status) => {
      const items = projects.filter((x) => x.status === status)
      return <div className="hk-column" key={status}><h4>{status} ({items.length})</h4>
        {items.map((row) => <div key={row.id} className="hk-card" onClick={() => onRowClick(row.id)}>
          <strong>{row.project_code}</strong><div>{row.title}</div>
          <div className="badge-row"><span className={`badge ${priorityClass(row.priority)}`}>{row.priority}</span></div>
          <div>{row.progress_percentage}%</div>
          {isProjectOverdue(row.planned_end_date, row.status) ? <div className="error-text">Overdue</div> : null}
        </div>)}
      </div>
    })}</div>
  }

  return <div className="table-wrap"><table className="data-table"><thead><tr>
    <th>Project Code</th><th>Title</th><th>Type</th><th>Property</th><th>Department</th><th>Owner</th><th>Manager</th><th>Priority</th><th>Status</th><th>Progress %</th><th>Planned End Date</th><th>Actual End Date</th><th>Updated At</th><th>Actions</th>
  </tr></thead><tbody>
    {projects.map((row) => <tr key={row.id} onClick={() => onRowClick(row.id)}>
      <td>{row.project_code}</td><td>{row.title}</td><td>{row.project_type}</td><td>{row.property_id || '-'}</td><td>{row.department_id || '-'}</td><td>{row.owner_id || '-'}</td><td>{row.manager_id || '-'}</td>
      <td><span className={`badge ${priorityClass(row.priority)}`}>{row.priority}</span></td>
      <td><span className="badge neutral">{row.status}</span></td>
      <td><progress max={100} value={row.progress_percentage} aria-label={`Progress ${row.progress_percentage}%`} /> {row.progress_percentage}%</td>
      <td>{row.planned_end_date || '-'} {isProjectOverdue(row.planned_end_date, row.status) ? <span className="error-text">Overdue</span> : null}</td>
      <td>{row.actual_end_date || '-'}</td><td>{new Date(row.updated_at).toLocaleString()}</td>
      <td><button className="button secondary small" onClick={(e) => e.stopPropagation()}>Open</button></td>
    </tr>)}
  </tbody></table></div>
}
