import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useAcknowledgeIntegrationAlert, useIntegrationAlerts, useResolveIntegrationAlert } from '../hooks/useIntegrations'

export function IntegrationAlertsPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const [query] = useState({ page: 1, page_size: 100 })
  const { data, loading, error, reload } = useIntegrationAlerts(auth?.accessToken, auth?.user?.org_id, query)
  const acknowledge = useAcknowledgeIntegrationAlert()
  const resolve = useResolveIntegrationAlert()
  const onAction = async (id: string, action: 'ack' | 'resolve') => {
    if (!auth?.accessToken || !auth.user?.org_id) return
    if (action === 'ack') await acknowledge(auth.accessToken, id, { org_id: auth.user.org_id })
    else await resolve(auth.accessToken, id, { org_id: auth.user.org_id })
    reload()
  }

  return <div className='page full'><div className='glass panel'><h2>Integration Alerts</h2>
    {loading ? <p>Loading alerts...</p> : null}
    {error ? <p className='error-text'>{error}</p> : null}
    <div className='table-wrap'><table className='data-table'><thead><tr><th>Severity</th><th>Provider</th><th>Alert Type</th><th>Message</th><th>Related Job</th><th>Status</th><th>Created At</th><th>Actions</th></tr></thead><tbody>{(data?.results || []).map((a) => <tr key={a.id}><td>{a.severity}</td><td>{a.provider}</td><td>{a.alert_type}</td><td>{a.message}</td><td>{a.related_job || '-'}</td><td>{a.status}</td><td>{a.created_at ? new Date(a.created_at).toLocaleString() : '-'}</td><td><button className='button secondary small' disabled={a.status !== 'OPEN'} onClick={() => void onAction(a.id, 'ack')}>Acknowledge</button> <button className='button secondary small' disabled={a.status === 'RESOLVED'} onClick={() => void onAction(a.id, 'resolve')}>Resolve</button> <button className='button secondary small' onClick={() => navigate('/integrations/troubleshooting')}>Open troubleshooting guide</button> {a.related_job ? <button className='button secondary small' onClick={() => navigate(`/integrations/jobs/${a.related_job}`)}>Open job</button> : null}</td></tr>)}</tbody></table></div>
  </div></div>
}
