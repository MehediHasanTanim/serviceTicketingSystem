import { useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useSnaggingItemDetail } from '../hooks/useProjects'

export function SnaggingItemDetailPage() {
  const { snagId } = useParams()
  const { auth } = useAuth()
  const detail = useSnaggingItemDetail(auth?.accessToken, auth?.user?.org_id, Number(snagId))
  if (detail.loading) return <div className="page full"><div className="glass panel"><p>Loading snagging item...</p></div></div>
  if (!detail.data) return <div className="page full"><div className="glass panel"><p className="error-text">{detail.error || 'Not found'}</p></div></div>
  return <div className="page full"><div className="glass panel"><h2>{detail.data.snag_number} • {detail.data.title}</h2><pre>{JSON.stringify(detail.data, null, 2)}</pre></div></div>
}
