import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/authContext'

export function HomePage() {
  const { auth, logout } = useAuth()
  const navigate = useNavigate()

  const onSignOut = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="page">
      <div className="glass card" style={{ width: 'min(560px, 92vw)' }}>
        <h2>Welcome back</h2>
        <p className="helper">Signed in as</p>
        <h3>{auth?.user?.display_name || auth?.userName || 'User'}</h3>
        <div className="hero-card" style={{ marginTop: '24px' }}>
          You are ready to manage service requests and operational workflows.
        </div>
        <button className="button secondary" style={{ marginTop: '24px' }} onClick={onSignOut}>
          Sign out
        </button>
      </div>
    </div>
  )
}
