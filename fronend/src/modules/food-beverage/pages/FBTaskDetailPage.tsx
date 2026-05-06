import { useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useFBTaskDetail } from '../hooks/useFoodBeverage'

export function FBTaskDetailPage() {
  const { id } = useParams(); const { auth } = useAuth(); const { data, loading, error } = useFBTaskDetail(auth?.accessToken, auth?.user?.org_id, Number(id))
  return <div className="page full"><div className="glass panel"><h2>F&B Task Detail</h2>{loading ? <p>Loading...</p> : null}{error ? <p className="error-text">{error}</p> : null}{data ? <div className="card-section"><p>{data.task_number}</p><p>{data.title}</p><p>Status: {data.status}</p><p>Assignee: {data.assigned_to || '-'}</p></div> : null}</div></div>
}
