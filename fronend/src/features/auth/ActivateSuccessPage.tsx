import { useNavigate } from 'react-router-dom'

export function ActivateSuccessPage() {
  const navigate = useNavigate()

  return (
    <div className="page">
      <div className="card">
        <h2>Account Activated</h2>
        <p className="helper">Your account is ready. You can now sign in.</p>
        <button className="button" onClick={() => navigate('/login')}>
          Go to Login
        </button>
      </div>
    </div>
  )
}
