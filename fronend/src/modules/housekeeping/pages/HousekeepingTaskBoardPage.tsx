import { useState } from 'react'
import { useAuth } from '../../../features/auth/authContext'
import { TaskBoard } from '../components/TaskBoard'
import {
  useCancelHousekeepingTask,
  useCompleteHousekeepingTask,
  useReopenHousekeepingTask,
  useStartHousekeepingTask,
  useVerifyHousekeepingTask,
} from '../hooks/useHousekeepingTaskActions'
import { useHousekeepingTasks } from '../hooks/useHousekeepingTasks'
import type { HousekeepingTaskFilters } from '../types/housekeeping.types'

const baseFilters: HousekeepingTaskFilters = { date: '', property: '', floor: '', room: '', staff: '', priority: '', taskType: '', status: '', q: '' }

export function HousekeepingTaskBoardPage() {
  const { auth } = useAuth()
  const [filters, setFilters] = useState<HousekeepingTaskFilters>(baseFilters)
  const { data, loading, error, reload } = useHousekeepingTasks(auth?.accessToken, auth?.user?.org_id, filters)
  const startTask = useStartHousekeepingTask(auth?.accessToken)
  const completeTask = useCompleteHousekeepingTask(auth?.accessToken)
  const verifyTask = useVerifyHousekeepingTask(auth?.accessToken)
  const cancelTask = useCancelHousekeepingTask(auth?.accessToken)
  const reopenTask = useReopenHousekeepingTask(auth?.accessToken)

  const runAction = async (taskId: string, action: 'start' | 'complete' | 'verify' | 'cancel' | 'reopen') => {
    const payload = { org_id: auth?.user?.org_id, note: action, reason: action }
    const id = Number(taskId)
    if (action === 'start') await startTask.mutate(id, payload)
    if (action === 'complete') await completeTask.mutate(id, payload)
    if (action === 'verify') await verifyTask.mutate(id, payload)
    if (action === 'cancel') await cancelTask.mutate(id, payload)
    if (action === 'reopen') await reopenTask.mutate(id, payload)
    await reload()
  }

  return (
    <div className="page full"><div className="glass panel"><div className="section-head"><h2>Housekeeping Task Board</h2><button className="button secondary small" onClick={reload}>Refresh</button></div>
      <div className="grid-form filters-grid">
        <input className="input" type="date" value={filters.date} onChange={(e) => setFilters((p) => ({ ...p, date: e.target.value }))} />
        <input className="input" placeholder="Staff ID" value={filters.staff} onChange={(e) => setFilters((p) => ({ ...p, staff: e.target.value }))} />
        <input className="input" placeholder="Search room/task" value={filters.q} onChange={(e) => setFilters((p) => ({ ...p, q: e.target.value }))} />
      </div>
      <TaskBoard tasks={data} loading={loading} error={error} onRetry={reload} onAction={runAction} />
    </div></div>
  )
}
