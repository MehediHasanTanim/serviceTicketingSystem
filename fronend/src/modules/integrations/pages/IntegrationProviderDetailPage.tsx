import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { SafeJson, StatusBadge } from '../components/common'
import { useIntegrationProviderDetail } from '../hooks/useIntegrations'

export function IntegrationProviderDetailPage() {
  const { id } = useParams()
  const { auth } = useAuth()
  const navigate = useNavigate()
  const { data, loading, error } = useIntegrationProviderDetail(auth?.accessToken, Number(id || 0))
  return <div className='page full'><div className='glass panel'><h2>Integration Provider Detail</h2>
    {loading ? <p>Loading provider...</p> : null}
    {error ? <p className='error-text'>{error}</p> : null}
    {data ? <><div className='card-section'><p><strong>Provider:</strong> {data.provider_code} - {data.name}</p><p><strong>Type:</strong> {data.provider_type}</p><p><strong>Status:</strong> <StatusBadge status={data.status} /></p><p><strong>Auth Type:</strong> {data.auth_type}</p><p><strong>Base URL:</strong> {data.base_url || '-'}</p><p><strong>Credentials Secret Ref:</strong> {data.credentials_secret_ref ? 'Configured' : 'Not configured'}</p></div>
      <div className='card-section'><h3>Config</h3><SafeJson value={data.config || {}} /></div>
      <div className='card-section'><h3>Retry Policy</h3><SafeJson value={data.retry_policy || {}} /></div>
      <div className='row-actions'><button className='button secondary' onClick={() => navigate(`/integrations/providers/${data.id}/edit`)}>Edit</button></div>
    </> : null}
  </div></div>
}
