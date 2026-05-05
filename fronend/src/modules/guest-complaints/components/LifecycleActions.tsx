import { useState } from 'react'
import type { ComplaintStatus } from '../types/guestComplaints.types'
import { allowedActions } from './utils'

type Props = {
  status: ComplaintStatus
  busy?: boolean
  onAction: (action: 'assign' | 'start' | 'escalate' | 'resolve' | 'confirm' | 'reopen' | 'void', reason?: string) => Promise<void> | void
}

export function LifecycleActions({ status, busy, onAction }: Props) {
  const actions = allowedActions(status)
  const [pending, setPending] = useState<string | null>(null)
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')
  const requiresReason = pending === 'reopen' || pending === 'void' || pending === 'escalate'
  const needsConfirm = ['reopen', 'void', 'escalate'].includes(String(pending))

  const run = async (action: Props['onAction'] extends (a: infer A, ...args: any) => any ? A : never) => {
    if (['reopen', 'void', 'escalate'].includes(action)) {
      setPending(action)
      setReason('')
      setError('')
      return
    }
    await onAction(action)
  }

  const confirm = async () => {
    if (!pending) return
    if (requiresReason && !reason.trim()) {
      setError('Reason is required.')
      return
    }
    await onAction(pending as any, reason.trim())
    setPending(null)
    setReason('')
  }

  return (
    <>
      <div className="status-actions">
        {actions.map((action) => <button key={action} className="button secondary small" disabled={busy} onClick={() => run(action)}>{action}</button>)}
        {actions.length === 0 ? <span className="hint">No lifecycle actions available</span> : null}
      </div>
      {needsConfirm ? (
        <div className="modal-backdrop" role="presentation">
          <div className="modal" role="dialog" aria-modal="true" aria-label="Lifecycle confirmation">
            <h3>Confirm {pending}</h3>
            {requiresReason ? <label className="field">Reason<textarea className="input" rows={3} value={reason} onChange={(e) => setReason(e.target.value)} /></label> : null}
            {error ? <p className="error-text">{error}</p> : null}
            <div className="modal-actions">
              <button className="button secondary small" onClick={() => setPending(null)}>Cancel</button>
              <button className="button small" disabled={busy} onClick={confirm}>Confirm</button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  )
}
