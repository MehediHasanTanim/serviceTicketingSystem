import { useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { ScoreSummary } from '../components/Scoring/ScoreSummary'
import { useInspectionRunDetail } from '../hooks/useInspections'

export function InspectionRunDetailPage() {
  const { id } = useParams()
  const { auth } = useAuth()
  const { data, loading, error } = useInspectionRunDetail(auth?.accessToken, auth?.user?.org_id, Number(id))

  return <div className="page full"><div className="glass panel"><h2>Inspection Run Detail</h2>
    {loading ? <p>Loading...</p> : null}
    {error ? <p className="error-text">{error}</p> : null}
    {data ? <>
      <div className="grid-form three"><div className="card-section"><strong>Inspection #</strong><p>{data.run.inspection_number}</p></div><div className="card-section"><strong>Status</strong><p>{data.run.status}</p></div><div className="card-section"><strong>Template</strong><p>{data.run.template_id}</p></div></div>
      <ScoreSummary finalScore={data.run.final_score} result={data.run.result} />
      <div className="card-section"><h3>History</h3><div className="table-wrap"><table className="data-table"><thead><tr><th>Timestamp</th><th>Action</th><th>Actor</th><th>Metadata</th></tr></thead><tbody>{data.history.map((row) => <tr key={row.id}><td>{new Date(row.created_at).toLocaleString()}</td><td>{row.action}</td><td>{row.actor_id || 'System'}</td><td><pre>{JSON.stringify(row.metadata, null, 2)}</pre></td></tr>)}</tbody></table></div></div>
    </> : null}
  </div></div>
}
