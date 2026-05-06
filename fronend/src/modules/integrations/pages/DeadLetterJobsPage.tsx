import { useAuth } from '../../../features/auth/authContext'
import { StatusBadge } from '../components/common'
import { useDeadLetterJobs } from '../hooks/useIntegrations'

export function DeadLetterJobsPage() {
  const { auth } = useAuth()
  const { data, loading, error } = useDeadLetterJobs(auth?.accessToken, auth?.user?.org_id)
  return <div className='page full'><div className='glass panel'><h2>Dead Letter Jobs</h2>
    {loading ? <p>Loading dead-letter jobs...</p> : null}
    {error ? <p className='error-text'>{error}</p> : null}
    <div className='table-wrap'><table className='data-table'><thead><tr><th>Correlation ID</th><th>Provider</th><th>Status</th><th>Error</th><th>Created</th></tr></thead><tbody>{(data?.results || []).map((row) => <tr key={row.id}><td>{row.correlation_id}</td><td>{row.provider_code || '-'}</td><td><StatusBadge status={row.status} /></td><td>{row.error_message || '-'}</td><td>{row.created_at ? new Date(row.created_at).toLocaleString() : '-'}</td></tr>)}</tbody></table></div>
  </div></div>
}
