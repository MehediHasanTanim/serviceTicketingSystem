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
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: '48px' }}>
      <div className="card" style={{ width: 'min(520px, 90vw)' }}>
        <h2>Welcome back</h2>
        <p className="helper">Signed in as</p>
        <h3>{auth?.user?.display_name || auth?.userName || 'User'}</h3>
        <button className="button secondary" style={{ marginTop: '24px' }} onClick={onSignOut}>
          Sign out
        </button>
      </div>
    </div>
  )
}
