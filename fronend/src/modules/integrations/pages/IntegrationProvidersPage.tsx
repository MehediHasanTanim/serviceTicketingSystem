import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useActivateIntegrationProvider, useDeactivateIntegrationProvider, useIntegrationProviders, useProviderHealthCheck } from '../hooks/useIntegrations'
import { StatusBadge } from '../components/common'
import type { IntegrationProvidersFilters } from '../types/integrations.types'

export function IntegrationProvidersPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const [filters, setFilters] = useState<IntegrationProvidersFilters>({ q: params.get('q') || '', provider_type: params.get('provider_type') || '', status: params.get('status') || '', auth_type: params.get('auth_type') || '', date_from: '', date_to: '', page: Number(params.get('page') || 1), page_size: 10, sort_by: 'updated_at', sort_dir: 'desc' })
  const { data, loading, error, reload } = useIntegrationProviders(auth?.accessToken, auth?.user?.org_id, filters)
  const activate = useActivateIntegrationProvider()
  const deactivate = useDeactivateIntegrationProvider()
  const healthCheck = useProviderHealthCheck()

  const sync = (next: IntegrationProvidersFilters) => { const p = new URLSearchParams(); Object.entries(next).forEach(([k, v]) => { if (v) p.set(k, String(v)) }); setParams(p, { replace: true }); setFilters(next) }
  const act = async (id: number, type: 'activate' | 'deactivate' | 'health') => {
    if (!auth?.accessToken || !auth.user?.org_id) return
    if (type === 'activate') await activate(auth.accessToken, id, { org_id: auth.user.org_id })
    if (type === 'deactivate') await deactivate(auth.accessToken, id, { org_id: auth.user.org_id })
    if (type === 'health') await healthCheck(auth.accessToken, id, { org_id: auth.user.org_id })
    reload()
  }

  return <div className='page full'><div className='glass panel'><h2>Integration Providers</h2>
    <div className='grid-form three'><input aria-label='Search providers' className='input' placeholder='Search by code/name/url' value={filters.q} onChange={(e) => sync({ ...filters, q: e.target.value, page: 1 })} /><input className='input' placeholder='Type' value={filters.provider_type} onChange={(e) => sync({ ...filters, provider_type: e.target.value, page: 1 })} /><input className='input' placeholder='Auth type' value={filters.auth_type} onChange={(e) => sync({ ...filters, auth_type: e.target.value, page: 1 })} /></div>
    <div className='row-actions'><button className='button' onClick={() => navigate('/integrations/providers/new')}>New Provider</button></div>
    {loading ? <p>Loading providers...</p> : null}
    {error ? <p className='error-text'>{error}</p> : null}
    <div className='table-wrap'><table className='data-table'><thead><tr><th>Provider Code</th><th>Name</th><th>Type</th><th>Status</th><th>Auth Type</th><th>Base URL</th><th>Last Health Check</th><th>Last Success</th><th>Last Failure</th><th>Updated At</th><th>Actions</th></tr></thead><tbody>
      {(data?.results || []).map((row) => <tr key={row.id}><td>{row.provider_code}</td><td>{row.name}</td><td>{row.provider_type}</td><td><StatusBadge status={row.status} /></td><td>{row.auth_type}</td><td>{row.base_url || '-'}</td><td>{row.last_health_check ? new Date(row.last_health_check).toLocaleString() : '-'}</td><td>{row.last_success ? new Date(row.last_success).toLocaleString() : '-'}</td><td>{row.last_failure ? new Date(row.last_failure).toLocaleString() : '-'}</td><td>{row.updated_at ? new Date(row.updated_at).toLocaleString() : '-'}</td><td><button className='button secondary small' onClick={() => void act(row.id, 'activate')}>Activate</button> <button className='button secondary small' onClick={() => void act(row.id, 'deactivate')}>Deactivate</button> <button className='button secondary small' onClick={() => void act(row.id, 'health')}>Health Check</button> <button className='button secondary small' onClick={() => navigate(`/integrations/providers/${row.id}/edit`)}>Edit</button> <button className='button secondary small' onClick={() => navigate(`/integrations/jobs?provider=${encodeURIComponent(row.provider_code || '')}`)}>View Logs</button></td></tr>)}
      {(!loading && (data?.results || []).length === 0) ? <tr><td colSpan={11}>No providers found.</td></tr> : null}
    </tbody></table></div>
  </div></div>
}
