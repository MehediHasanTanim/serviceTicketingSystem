import type { HousekeepingTaskLike, HousekeepingTaskStatus } from '../types/housekeeping.types'

const statuses: HousekeepingTaskStatus[] = ['PENDING', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'VERIFIED', 'CANCELLED']

export function TaskBoard({ tasks, loading, error, onRetry, onAction }: {
  tasks: HousekeepingTaskLike[]
  loading: boolean
  error: string
  onRetry: () => void
  onAction?: (taskId: string, action: 'start' | 'complete' | 'verify' | 'cancel' | 'reopen') => void
}) {
  if (loading) return <p className="helper">Loading housekeeping tasks...</p>
  if (error) return <div><p className="error">{error}</p><button className="button secondary small" onClick={onRetry}>Retry</button></div>
  if (tasks.length === 0) return <p className="helper">No housekeeping tasks found.</p>

  return (
    <div className="hk-board" aria-label="Housekeeping task board">
      {statuses.map((status) => {
        const rows = tasks.filter((task) => task.status === status)
        return (
          <section key={status} className="hk-column">
            <h3>{status} ({rows.length})</h3>
            {rows.map((task) => (
              <article key={task.id} className="hk-card">
                <strong>Room {task.roomNumber}</strong>
                <p>{task.taskType}</p>
                <p><span className={`badge ${task.priority.toLowerCase()}`}>{task.priority}</span> <span className="badge neutral">{task.status}</span></p>
                <p>{task.assignedStaff || 'Unassigned'}</p>
                <p>{task.dueAt ? new Date(task.dueAt).toLocaleString() : '-'}</p>
                {task.overdue ? <p className="error">Overdue</p> : null}
                <div className="status-actions">
                  {task.status === 'PENDING' || task.status === 'ASSIGNED' ? <button className="button secondary small" onClick={() => onAction?.(task.id, 'start')}>Start</button> : null}
                  {task.status === 'IN_PROGRESS' ? <button className="button secondary small" onClick={() => onAction?.(task.id, 'complete')}>Complete</button> : null}
                  {task.status === 'COMPLETED' ? <button className="button secondary small" onClick={() => onAction?.(task.id, 'verify')}>Verify</button> : null}
                  {task.status !== 'CANCELLED' && task.status !== 'COMPLETED' && task.status !== 'VERIFIED' ? (
                    <button className="button secondary small" onClick={() => onAction?.(task.id, 'cancel')}>Cancel</button>
                  ) : null}
                  {task.status === 'COMPLETED' || task.status === 'CANCELLED' || task.status === 'VERIFIED' ? (
                    <button className="button secondary small" onClick={() => onAction?.(task.id, 'reopen')}>Reopen</button>
                  ) : null}
                </div>
              </article>
            ))}
          </section>
        )
      })}
    </div>
  )
}
