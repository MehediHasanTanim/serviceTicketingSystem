import type { TimelineItem } from '../types'
import { toTimelineOrder } from '../utils'

type Props = { entries: TimelineItem[] }

export function TimelineView({ entries }: Props) {
  const ordered = toTimelineOrder(entries)
  if (ordered.length === 0) return <p className="hint">No timeline items yet.</p>

  return (
    <ul className="timeline-list" aria-label="Timeline">
      {ordered.map((entry) => (
        <li key={entry.id} className="timeline-item">
          <div className="timeline-icon" aria-hidden="true">•</div>
          <div>
            <div><strong>{entry.summary}</strong></div>
            <div className="hint">{entry.actor} • {new Date(entry.at).toLocaleString()}</div>
            {entry.note ? <div>{entry.note}</div> : null}
          </div>
        </li>
      ))}
    </ul>
  )
}
