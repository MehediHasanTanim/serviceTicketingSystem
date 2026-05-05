import type { ApprovalTrailEntry } from '../types/riskCompliance.types'

export function ApprovalTrail({ entries, canManage, onApprove, onReject }: { entries: ApprovalTrailEntry[]; canManage?: boolean; onApprove?: () => void; onReject?: () => void }) {
  return (
    <div className="card-section">
      <h3>Approval Trail</h3>
      {entries.length === 0 ? <p className="hint">No approval events yet.</p> : null}
      <div className="list">
        {entries.map((entry, index) => (
          <div key={`${entry.timestamp}-${index}`} className="list-item" role="listitem">
            <div><strong>{entry.approver}</strong> - {entry.decision}</div>
            <div className="muted">{new Date(entry.timestamp).toLocaleString()} - {entry.comment || 'No comment'}</div>
            <span className="badge neutral">{entry.status}</span>
          </div>
        ))}
      </div>
      {canManage ? (
        <div className="row-actions" style={{ marginTop: '12px' }}>
          <button className="button secondary small" onClick={onApprove}>Approve</button>
          <button className="button secondary small" onClick={onReject}>Reject</button>
        </div>
      ) : null}
    </div>
  )
}
