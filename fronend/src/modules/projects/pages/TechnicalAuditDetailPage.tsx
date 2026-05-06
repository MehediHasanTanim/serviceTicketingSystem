import { useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useTechnicalAuditDetail } from '../hooks/useProjects'

export function TechnicalAuditDetailPage() {
  const { auditId } = useParams()
  const { auth } = useAuth()
  const detail = useTechnicalAuditDetail(auth?.accessToken, auth?.user?.org_id, Number(auditId))
  if (detail.loading) return <div className="page full"><div className="glass panel"><p>Loading technical audit...</p></div></div>
  if (!detail.data) return <div className="page full"><div className="glass panel"><p className="error-text">{detail.error || 'Not found'}</p></div></div>
  return <div className="page full"><div className="glass panel"><h2>{detail.data.audit_number} • {detail.data.title}</h2><pre>{JSON.stringify(detail.data, null, 2)}</pre></div></div>
}
