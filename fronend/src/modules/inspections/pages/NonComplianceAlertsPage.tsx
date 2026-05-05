import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useAcknowledgeNonComplianceAlert, useNonComplianceAlerts, useResolveNonComplianceAlert } from '../hooks/useInspections'

export function NonComplianceAlertsPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const { data, loading, error, reload } = useNonComplianceAlerts(auth?.accessToken, auth?.user?.org_id)
  const acknowledge = useAcknowledgeNonComplianceAlert()
  const resolve = useResolveNonComplianceAlert()
  const [activeId, setActiveId] = useState<number | null>(null)
  const active = (data?.results || []).find((x) => x.id === activeId)

  const takeAction = async (id: number, type: 'ack' | 'resolve') => {
    if (!auth?.accessToken || !auth.user?.org_id) return
    if (type === 'resolve' && !window.confirm('Resolve this alert?')) return
    if (type === 'ack') await acknowledge(auth.accessToken, id, { org_id: auth.user.org_id })
    else await resolve(auth.accessToken, id, { org_id: auth.user.org_id })
    reload()
  }

  return <div className="page full"><div className="glass panel"><h2>Non-Compliance Alerts</h2>
    {loading ? <p>Loading alerts...</p> : null}
    {error ? <p className="error-text">{error}</p> : null}
    <div className="table-wrap"><table className="data-table"><thead><tr><th>Alert Type</th><th>Severity</th><th>Inspection #</th><th>Checklist Item</th><th>Assigned To</th><th>Status</th><th>Created At</th><th>Actions</th></tr></thead><tbody>
      {(data?.results || []).map((row) => <tr key={row.id} className={row.status !== 'RESOLVED' && (row.severity === 'HIGH' || row.severity === 'CRITICAL') ? 'row-critical' : ''}><td>{row.alert_type}</td><td>{row.severity}</td><td>{row.inspection_run_id}</td><td>{row.checklist_item_id || '-'}</td><td>{row.assigned_to || '-'}</td><td>{row.status}</td><td>{new Date(row.created_at).toLocaleString()}</td><td><button className="button secondary small" disabled={row.status !== 'OPEN'} onClick={() => takeAction(row.id, 'ack')}>Acknowledge</button> <button className="button secondary small" disabled={row.status === 'RESOLVED'} onClick={() => takeAction(row.id, 'resolve')}>Resolve</button> <button className="button secondary small" onClick={() => navigate(`/inspections/runs/${row.inspection_run_id}`)}>Run</button> <button className="button secondary small" onClick={() => setActiveId(row.id)}>Detail</button></td></tr>)}
    </tbody></table></div>
    {active ? <div className="card-section"><h3>Alert Detail</h3><pre>{JSON.stringify(active, null, 2)}</pre><button className="button secondary small" onClick={() => setActiveId(null)}>Close</button></div> : null}
  </div></div>
}
