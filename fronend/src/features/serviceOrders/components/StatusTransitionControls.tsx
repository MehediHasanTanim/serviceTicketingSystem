import { useMemo, useState } from 'react'
import type { ServiceOrderStatus } from '../types'
import { getAllowedActions } from '../utils'

type Props = {
  status: ServiceOrderStatus
  busy?: boolean
  onAction: (action: 'assign' | 'start' | 'hold' | 'complete' | 'defer' | 'void' | 'reassign', reason?: string) => Promise<void> | void
}

const needsReason = new Set(['defer', 'void'])
const needsConfirm = new Set(['complete', 'defer', 'void'])

export function StatusTransitionControls({ status, busy, onAction }: Props) {
  const actions = useMemo(() => getAllowedActions(status), [status])
  const [confirmAction, setConfirmAction] = useState<string | null>(null)
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')

  const run = async (action: Props['onAction'] extends (a: infer A, ...args: any) => any ? A : never) => {
    if (needsConfirm.has(action)) {
      setConfirmAction(action)
      setError('')
      if (!needsReason.has(action)) setReason('')
      return
    }
    await onAction(action)
  }

  const confirm = async () => {
    if (!confirmAction) return
    if (needsReason.has(confirmAction) && !reason.trim()) {
      setError('Reason is required.')
      return
    }
    await onAction(confirmAction as any, reason.trim())
    setConfirmAction(null)
    setReason('')
    setError('')
  }

  return (
    <div>
      <div className="status-actions">
        {actions.map((action) => (
          <button key={action} className="button secondary small" disabled={busy} onClick={() => run(action)}>
            {action === 'reassign' ? 'Reassign' : action.charAt(0).toUpperCase() + action.slice(1)}
          </button>
        ))}
        {actions.length === 0 ? <span className="hint">No available actions</span> : null}
      </div>
      {confirmAction ? (
        <div className="modal-backdrop" role="presentation">
          <div className="modal" role="dialog" aria-modal="true" aria-label="Confirm action">
            <h3>Confirm {confirmAction}</h3>
            {needsReason.has(confirmAction) ? (
              <label className="field" htmlFor="transition-reason">
                Reason
                <textarea
                  id="transition-reason"
                  className="input"
                  value={reason}
                  onChange={(event) => setReason(event.target.value)}
                  rows={3}
                />
              </label>
            ) : null}
            {error ? <p className="error-text">{error}</p> : null}
            <div className="modal-actions">
              <button type="button" className="button secondary small" onClick={() => setConfirmAction(null)}>Cancel</button>
              <button type="button" className="button small" onClick={confirm} disabled={busy}>Confirm</button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
