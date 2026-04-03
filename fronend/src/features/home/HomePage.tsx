import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/authContext'
import { apiRequest } from '../../shared/api/client'

export function HomePage() {
  const { auth, logout } = useAuth()
  const navigate = useNavigate()
  const [activeMenu, setActiveMenu] = useState<'users' | 'profile' | 'security'>('users')
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
            <button
              className={`menu-item ${activeMenu === 'users' ? 'active' : ''}`}
              onClick={() => setActiveMenu('users')}
            >
              Users
            </button>
            <button
              className={`menu-item ${activeMenu === 'profile' ? 'active' : ''}`}
              onClick={() => setActiveMenu('profile')}
            >
              Profile
            </button>
            <button
              className={`menu-item ${activeMenu === 'security' ? 'active' : ''}`}
              onClick={() => setActiveMenu('security')}
            >
              Security
            </button>
          </div>
          <button className="button secondary" onClick={onSignOut}>
            Sign out
          </button>
        </aside>
        <section className="glass card">
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
          {activeMenu === 'profile' && (
            <>
              <h2>Profile</h2>
              <p className="helper">Signed in as</p>
              <h3>{displayName}</h3>
              <div className="hero-card" style={{ marginTop: '24px' }}>
                Manage profile settings in upcoming releases.
              </div>
            </>
          )}
          {activeMenu === 'security' && (
            <>
              <h2>Security</h2>
              <p className="helper">Manage your access and security preferences.</p>
              <div className="hero-card" style={{ marginTop: '24px' }}>
                Security controls will appear here.
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  )
}
