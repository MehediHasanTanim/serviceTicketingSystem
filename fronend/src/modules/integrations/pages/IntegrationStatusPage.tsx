import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { NumberSafe, StatusBadge } from '../components/common'
import { useIntegrationMetricsSummary, useIntegrationProviders, useProviderHealthCheck } from '../hooks/useIntegrations'

export function IntegrationStatusPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const { data: metrics, loading, error, reload } = useIntegrationMetricsSummary(auth?.accessToken, auth?.user?.org_id)
  const { data: providers } = useIntegrationProviders(auth?.accessToken, auth?.user?.org_id, { q: '', provider_type: '', status: '', auth_type: '', date_from: '', date_to: '', page: 1, page_size: 100, sort_by: 'updated_at', sort_dir: 'desc' })
  const healthCheck = useProviderHealthCheck()
  const runHealth = async (id: number) => { if (!auth?.accessToken || !auth.user?.org_id) return; await healthCheck(auth.accessToken, id, { org_id: auth.user.org_id }); reload() }

  return <div className='page full'><div className='glass panel'><h2>Integration Health Dashboard</h2>
    {loading ? <p>Loading health metrics...</p> : null}
    {error ? <div><p className='error-text'>{error}</p><button className='button secondary small' onClick={() => reload()}>Retry</button></div> : null}
    <div className='grid-cards'>{[['Total providers', metrics?.total_providers], ['Active providers', metrics?.active_providers], ['Providers in error', metrics?.providers_in_error], ['Total jobs', metrics?.total_jobs], ['Successful jobs', metrics?.successful_jobs], ['Failed jobs', metrics?.failed_jobs], ['Retrying jobs', metrics?.retrying_jobs], ['Dead-letter jobs', metrics?.dead_letter_jobs], ['Success rate', metrics?.success_rate], ['Average duration(ms)', metrics?.avg_duration_ms]].map(([k, v]) => <div key={String(k)} className='card-section'><strong>{k}</strong><p><NumberSafe value={v} /></p></div>)}</div>
    <div className='table-wrap'><table className='data-table'><thead><tr><th>Provider</th><th>Type</th><th>Status</th><th>Last Health Check</th><th>Last Success</th><th>Last Failure</th><th>Actions</th></tr></thead><tbody>{(providers?.results || []).map((p) => <tr key={p.id}><td>{p.name}</td><td>{p.provider_type}</td><td><StatusBadge status={p.status} /></td><td>{p.last_health_check ? new Date(p.last_health_check).toLocaleString() : '-'}</td><td>{p.last_success ? new Date(p.last_success).toLocaleString() : '-'}</td><td>{p.last_failure ? new Date(p.last_failure).toLocaleString() : '-'}</td><td><button className='button secondary small' onClick={() => void runHealth(p.id)}>Run health check</button> <button className='button secondary small' onClick={() => navigate('/integrations/troubleshooting')}>Troubleshoot</button> <button className='button secondary small' onClick={() => navigate(`/integrations/providers/${p.id}`)}>Provider</button> <button className='button secondary small' onClick={() => navigate('/integrations/jobs')}>Sync logs</button></td></tr>)}</tbody></table></div>
  </div></div>
}
