import { useMemo, useState } from 'react'

type UserOption = { id: number; label: string }

type Props = {
  open: boolean
  currentAssigneeId?: number | null
  users: UserOption[]
  busy?: boolean
  reassign?: boolean
  onClose: () => void
  onSubmit: (assigneeId: number, reason?: string) => Promise<void> | void
}

export function AssignmentModal({ open, currentAssigneeId, users, busy, reassign, onClose, onSubmit }: Props) {
  const [search, setSearch] = useState('')
  const [assigneeId, setAssigneeId] = useState<number | ''>('')
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')

  const options = useMemo(
    () => users.filter((u) => u.label.toLowerCase().includes(search.toLowerCase())),
    [users, search],
  )

  if (!open) return null

  const submit = async () => {
    if (!assigneeId) {
      setError('Please select an assignee.')
      return
    }
    if (currentAssigneeId && assigneeId === currentAssigneeId) {
      setError('Please select a different assignee.')
      return
    }
    if (reassign && !reason.trim()) {
      setError('Reason is required for reassignment.')
      return
    }
    await onSubmit(assigneeId, reason.trim() || undefined)
    setSearch('')
    setReason('')
    setAssigneeId('')
    setError('')
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <div className="modal" role="dialog" aria-modal="true" aria-label={reassign ? 'Reassign order' : 'Assign order'}>
        <h3>{reassign ? 'Reassign Order' : 'Assign Order'}</h3>
        <label className="field" htmlFor="assignee-search">
          Search users
          <input id="assignee-search" className="input" value={search} onChange={(e) => setSearch(e.target.value)} />
        </label>
        <label className="field" htmlFor="assignee-select">
          Assignee
          <select
            id="assignee-select"
            className="input"
            value={assigneeId}
            onChange={(e) => setAssigneeId(e.target.value ? Number(e.target.value) : '')}
          >
            <option value="">Select user</option>
            {options.map((user) => (
              <option key={user.id} value={user.id}>{user.label}</option>
            ))}
          </select>
        </label>
        <label className="field" htmlFor="assignee-reason">
          Reason {reassign ? '(recommended)' : '(optional)'}
          <textarea id="assignee-reason" className="input" rows={3} value={reason} onChange={(e) => setReason(e.target.value)} />
        </label>
        {error ? <p className="error-text">{error}</p> : null}
        <div className="modal-actions">
          <button type="button" className="button secondary small" onClick={onClose}>Cancel</button>
          <button type="button" className="button small" onClick={submit} disabled={busy}>Submit</button>
        </div>
      </div>
    </div>
  )
}
