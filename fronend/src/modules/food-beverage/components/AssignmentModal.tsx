import { useMemo, useState } from 'react'

type Staff = { id: number; label: string }

export function AssignmentModal({ open, currentAssigneeId, onClose, onSubmit, staff, saving }: { open: boolean; currentAssigneeId?: number | null; onClose: () => void; onSubmit: (assignee: number, reason: string) => Promise<void> | void; staff: Staff[]; saving?: boolean }) {
  const [search, setSearch] = useState('')
  const [assignee, setAssignee] = useState('')
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')
  const options = useMemo(() => staff.filter((s) => s.label.toLowerCase().includes(search.toLowerCase())), [staff, search])
  if (!open) return null

  const submit = async () => {
    setError('')
    if (!assignee) return setError('Assignee is required.')
    const id = Number(assignee)
    if (id === currentAssigneeId) return setError('Please select a different assignee.')
    await onSubmit(id, reason.trim())
  }

  return <div className="modal-backdrop" role="presentation"><div className="modal" role="dialog" aria-modal="true" aria-label="Assign task">
    <h3>Assign / Reassign Task</h3>
    <label className="field">Search staff<input className="input" aria-label="Search staff" value={search} onChange={(e) => setSearch(e.target.value)} /></label>
    <label className="field">Assignee<select className="input" aria-label="Assignee" value={assignee} onChange={(e) => setAssignee(e.target.value)}><option value="">Select assignee</option>{options.map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}</select></label>
    <label className="field">Reason<textarea className="input" aria-label="Reason" rows={2} value={reason} onChange={(e) => setReason(e.target.value)} /></label>
    {error ? <p className="error-text">{error}</p> : null}
    <div className="modal-actions"><button className="button secondary small" onClick={onClose}>Close</button><button className="button small" disabled={saving} onClick={() => void submit()}>{saving ? 'Saving...' : 'Submit'}</button></div>
  </div></div>
}
