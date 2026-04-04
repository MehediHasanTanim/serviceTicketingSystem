import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/authContext'
import { apiRequest } from '../../shared/api/client'

export function HomePage() {
  const { auth, logout } = useAuth()
  const navigate = useNavigate()
  const [activeMenu, setActiveMenu] = useState<'dashboard' | 'users' | 'roles'>('users')
  const [users, setUsers] = useState<Array<{ id: number; display_name: string; email: string; status: string }>>([])
  const [loadingUsers, setLoadingUsers] = useState(false)
  const [usersError, setUsersError] = useState('')

  const onSignOut = async () => {
    await logout()
    navigate('/login')
  }

  useEffect(() => {
    const loadUsers = async () => {
      if (!auth?.accessToken || !auth?.user?.org_id) return
      setLoadingUsers(true)
      setUsersError('')
      try {
        const data = await apiRequest(`/users?org_id=${auth.user.org_id}`, {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${auth.accessToken}`,
          },
        })
        setUsers(data || [])
      } catch (err: any) {
        setUsersError(err.details?.detail || err.message)
      } finally {
        setLoadingUsers(false)
      }
    }
    loadUsers()
  }, [auth?.accessToken, auth?.user?.org_id])

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
        <aside className="sidebar-lite">
          <div className="brand">
            <div className="avatar">{initials}</div>
            <div>
              <div className="brand-title">Service Ticketing</div>
              <div className="brand-sub">{displayName}</div>
            </div>
          </div>
          <nav className="menu">
            <button
              className={`menu-item ${activeMenu === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveMenu('dashboard')}
            >
              <span className="icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
                  <path d="M4 7h6v6H4zM14 7h6v6h-6zM4 17h6v3H4zM14 17h6v3h-6z" />
                </svg>
              </span>
              <span>Dashboard</span>
            </button>
            <button
              className={`menu-item ${activeMenu === 'users' ? 'active' : ''}`}
              onClick={() => setActiveMenu('users')}
            >
              <span className="icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
                  <path d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4Z" />
                  <path d="M4 20a8 8 0 0 1 16 0" />
                </svg>
              </span>
              <span>User Management</span>
            </button>
            <button
              className={`menu-item ${activeMenu === 'roles' ? 'active' : ''}`}
              onClick={() => setActiveMenu('roles')}
            >
              <span className="icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
                  <path d="M5 9l7-4 7 4-7 4-7-4Z" />
                  <path d="M5 9v6l7 4 7-4V9" />
                </svg>
              </span>
              <span>Role Management</span>
            </button>
          </nav>
          <button className="logout" onClick={onSignOut}>
            <span className="icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
                <path d="M10 17l5-5-5-5" />
                <path d="M15 12H3" />
              </svg>
            </span>
            Logout
          </button>
        </aside>
        <section className="glass card">
          {activeMenu === 'dashboard' && (
            <>
              <h2>Dashboard</h2>
              <p className="helper">Dashboard will be implemented in upcoming release.</p>
              <div className="hero-card" style={{ marginTop: '24px' }}>
                Coming soon.
              </div>
            </>
          )}
          {activeMenu === 'users' && (
            <>
              <h2>User Directory</h2>
              <p className="helper">Manage users in your organization.</p>
              {loadingUsers && <p className="helper">Loading users...</p>}
              {usersError && <p className="error">{usersError}</p>}
              {!loadingUsers && !usersError && (
                <div className="list">
                  {users.map((user) => (
                    <div key={user.id} className="list-item">
                      <div>
                        <strong>{user.display_name}</strong>
                        <div className="helper">{user.email}</div>
                      </div>
                      <span className={`status ${user.status}`}>{user.status}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
          {activeMenu === 'roles' && (
            <>
              <h2>Role Management</h2>
              <p className="helper">Role Management will be implemented in upcoming release.</p>
              <div className="hero-card" style={{ marginTop: '24px' }}>
                Coming soon.
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  )
}
