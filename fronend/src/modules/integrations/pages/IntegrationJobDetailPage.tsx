import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { SafeJson, StatusBadge } from '../components/common'
import { useIntegrationJobDetail, useMoveIntegrationJobToDeadLetter, useRetryIntegrationJob } from '../hooks/useIntegrations'

export function IntegrationJobDetailPage() {
  const { id } = useParams()
  const { auth } = useAuth()
  const { data, loading, error, reload } = useIntegrationJobDetail(auth?.accessToken, auth?.user?.org_id, Number(id || 0))
  const retry = useRetryIntegrationJob()
  const dead = useMoveIntegrationJobToDeadLetter()
  const [submitting, setSubmitting] = useState(false)

  const onRetry = async () => {
    if (!auth?.accessToken || !auth.user?.org_id || !data?.id) return
    if (!window.confirm('Retry this job?')) return
    setSubmitting(true)
    await retry(auth.accessToken, data.id, { org_id: auth.user.org_id })
    setSubmitting(false)
    reload()
  }

  const onDead = async () => {
    if (!auth?.accessToken || !auth.user?.org_id || !data?.id) return
    if (!window.confirm('Move this job to dead letter?')) return
    setSubmitting(true)
    await dead(auth.accessToken, data.id, { org_id: auth.user.org_id })
    setSubmitting(false)
    reload()
  }

  return <div className='page full'><div className='glass panel'><h2>Integration Job Detail</h2>
    {loading ? <p>Loading job...</p> : null}
    {error ? <p className='error-text'>{error}</p> : null}
    {data ? <><div className='card-section'><h3>Overview</h3><p><strong>Correlation ID:</strong> {data.correlation_id}</p><p><strong>Status:</strong> <StatusBadge status={data.status} /></p><p><strong>Error code:</strong> {data.error_code || '-'}</p><p><strong>Error message:</strong> {data.error_message || '-'}</p></div>
      <div className='row-actions'><button className='button secondary' disabled={submitting} onClick={() => void onRetry()}>Retry job</button> <button className='button secondary' disabled={submitting} onClick={() => void onDead()}>Move to dead letter</button></div>
      <div className='card-section'><h3>Request Payload</h3><SafeJson value={data.request_payload || {}} /></div>
      <div className='card-section'><h3>Response Payload</h3><SafeJson value={data.response_payload || {}} /></div>
      <div className='card-section'><h3>Retry History / Attempts</h3><div role='list'>{(data.attempts || []).map((a, idx) => <div key={`${a.at}-${idx}`} role='listitem'>{new Date(a.at).toLocaleString()} - {a.status} {a.error_message ? `- ${a.error_message}` : ''}</div>)}</div></div>
    </> : null}
  </div></div>
}
