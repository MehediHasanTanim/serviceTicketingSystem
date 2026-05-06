import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { StatusBadge } from '../components/common'
import { useIntegrationJobs } from '../hooks/useIntegrations'
import type { IntegrationJobsFilters } from '../types/integrations.types'

export function IntegrationJobsPage() {
  const { auth } = useAuth()
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const [filters, setFilters] = useState<IntegrationJobsFilters>({ provider: params.get('provider') || '', job_type: '', direction: '', status: '', source_entity_type: '', target_entity_type: '', date_from: '', date_to: '', correlation_id: params.get('correlation_id') || '', page: Number(params.get('page') || 1), page_size: 10 })
  const { data, loading, error } = useIntegrationJobs(auth?.accessToken, auth?.user?.org_id, filters)
  const sync = (next: IntegrationJobsFilters) => { const p = new URLSearchParams(); Object.entries(next).forEach(([k, v]) => { if (v) p.set(k, String(v)) }); setParams(p, { replace: true }); setFilters(next) }

  return <div className='page full'><div className='glass panel'><h2>Integration Jobs</h2>
    <div className='grid-form three'><input className='input' placeholder='Provider' value={filters.provider} onChange={(e) => sync({ ...filters, provider: e.target.value, page: 1 })} /><input className='input' placeholder='Status' value={filters.status} onChange={(e) => sync({ ...filters, status: e.target.value, page: 1 })} /><input className='input' placeholder='Correlation ID' value={filters.correlation_id} onChange={(e) => sync({ ...filters, correlation_id: e.target.value, page: 1 })} /></div>
    {loading ? <p>Loading jobs...</p> : null}
    {error ? <p className='error-text'>{error}</p> : null}
    <div className='table-wrap'><table className='data-table'><thead><tr><th>Correlation ID</th><th>Provider</th><th>Job Type</th><th>Direction</th><th>Status</th><th>Source Entity</th><th>Target Entity</th><th>Retry Count</th><th>Next Retry At</th><th>Started At</th><th>Completed At</th><th>Actions</th></tr></thead><tbody>{(data?.results || []).map((row) => <tr key={row.id}><td>{row.correlation_id || '-'}</td><td>{row.provider_code || row.provider_name || '-'}</td><td>{row.job_type || '-'}</td><td>{row.direction || '-'}</td><td><StatusBadge status={row.status} /></td><td>{row.source_entity_type || '-'}</td><td>{row.target_entity_type || '-'}</td><td>{row.retry_count || 0}</td><td>{row.next_retry_at ? new Date(row.next_retry_at).toLocaleString() : '-'}</td><td>{row.started_at ? new Date(row.started_at).toLocaleString() : '-'}</td><td>{row.completed_at ? new Date(row.completed_at).toLocaleString() : '-'}</td><td><button className='button secondary small' onClick={() => navigate(`/integrations/jobs/${row.id}`)}>View detail</button></td></tr>)}</tbody></table></div>
  </div></div>
}
