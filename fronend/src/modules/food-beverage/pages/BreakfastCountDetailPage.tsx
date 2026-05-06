import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useBreakfastCountDetail } from '../hooks/useFoodBeverage'

export function BreakfastCountDetailPage() {
  const { id } = useParams(); const { auth } = useAuth(); const navigate = useNavigate()
  const { data, loading, error } = useBreakfastCountDetail(auth?.accessToken, auth?.user?.org_id, Number(id))
  return <div className="page full"><div className="glass panel"><div className="section-head"><h2>Breakfast Count Detail</h2><button className="button secondary" onClick={() => navigate(`/food-beverage/breakfast-counts/${id}/edit`)}>Edit</button></div>
    {loading ? <p>Loading...</p> : null}{error ? <p className="error-text">{error}</p> : null}
    {data ? <div className="card-section"><p>Service Date: {data.service_date}</p><p>Property: {data.property_id}</p><p>Outlet: {data.outlet_id}</p><p>Expected: {data.expected_guest_count}</p><p>Actual: {data.actual_guest_count}</p><p>Variance: {data.actual_guest_count - data.expected_guest_count}</p><p>Notes: {data.notes || '-'}</p></div> : null}
  </div></div>
}
