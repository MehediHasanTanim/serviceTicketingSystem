import type { ProjectTimelineEvent } from '../types/projects.types'

export function ProjectTimeline({ events, loading, error }: { events: ProjectTimelineEvent[]; loading: boolean; error: string }) {
  if (loading) return <p>Loading timeline...</p>
  if (error) return <p className="error-text">{error}</p>
  if (!events.length) return <p className="hint">No timeline events found.</p>

  const sorted = [...events].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  return <ul className="timeline-list">{sorted.map((row) => <li key={row.id} className="timeline-item">
    <span className="timeline-icon">•</span>
    <div><strong>{row.event_type}</strong> • {new Date(row.created_at).toLocaleString()} • Actor {row.actor_id || 'System'}
      {row.previous_status || row.new_status ? <div>{row.previous_status || '-'} → {row.new_status || '-'}</div> : null}
      {typeof row.progress_percentage === 'number' ? <div>Progress: {row.progress_percentage}%</div> : null}
      {row.message ? <div>{row.message}</div> : null}
    </div>
  </li>)}</ul>
}
