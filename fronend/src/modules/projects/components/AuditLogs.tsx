import { useState } from 'react'
import type { AuditLog } from '../types/projects.types'

export function AuditLogs({ rows }: { rows: AuditLog[] }) {
  const [meta, setMeta] = useState<Record<string, unknown> | null>(null)
  return <>
    <div className="table-wrap"><table className="data-table"><thead><tr><th>Timestamp</th><th>Actor</th><th>Action</th><th>Entity Type</th><th>Entity ID</th><th>Details</th></tr></thead><tbody>
      {rows.map((row) => <tr key={row.id}><td>{new Date(row.created_at).toLocaleString()}</td><td>{row.actor_user_id || 'System'}</td><td>{row.action}</td><td>{row.target_type}</td><td>{row.target_id}</td><td><button className="button secondary small" onClick={() => setMeta(row.metadata)}>Open</button></td></tr>)}
    </tbody></table></div>
    {meta ? <div className="card-section"><h3>Metadata</h3><pre>{JSON.stringify(meta, null, 2)}</pre><button className="button secondary small" onClick={() => setMeta(null)}>Close</button></div> : null}
  </>
}
