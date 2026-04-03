import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/authContext'

export function HomePage() {
  const { auth, logout } = useAuth()
  const navigate = useNavigate()

  const onSignOut = async () => {
    await logout()
    navigate('/login')
  }

  const displayName = auth?.user?.display_name || auth?.userName || 'User'
  const initials = displayName
    .split(' ')
    .filter(Boolean)
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  return (
    <div className="page full">
      <div className="dashboard">
        <aside className="glass sidebar">
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div className="avatar">{initials}</div>
            <div>
              <div style={{ fontWeight: 700 }}>{displayName}</div>
              <div className="helper" style={{ fontSize: '0.8rem' }}>
                Logged in
              </div>
            </div>
          </div>
          <div className="menu">
            <div className="menu-item">User</div>
            <div className="menu-item">Profile</div>
            <div className="menu-item">Security</div>
          </div>
          <button className="button secondary" onClick={onSignOut}>
            Sign out
          </button>
        </aside>
        <section className="glass card">
          <h2>Welcome back</h2>
          <p className="helper">Signed in as</p>
          <h3>{displayName}</h3>
          <div className="hero-card" style={{ marginTop: '24px' }}>
            You are ready to manage service requests and operational workflows.
          </div>
        </section>
      </div>
    </div>
  )
}
