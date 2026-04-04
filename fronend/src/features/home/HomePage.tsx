import { type ChangeEvent, type FormEvent, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/authContext'
import { apiRequest } from '../../shared/api/client'

export function HomePage() {
  const { auth, logout } = useAuth()
  const navigate = useNavigate()
  const [activeMenu, setActiveMenu] = useState<'dashboard' | 'users' | 'roles'>('users')
  const [users, setUsers] = useState<Array<{ id: number; display_name: string; email: string; status: string; roles?: string[] }>>([])
  const [showCreate, setShowCreate] = useState(false)
  const [roles, setRoles] = useState<Array<{ id: number; name: string }>>([])
  const [createError, setCreateError] = useState('')
  const [createLoading, setCreateLoading] = useState(false)
  const [createForm, setCreateForm] = useState({
    email: '',
    display_name: '',
    phone: '',
    status: 'invited',
    role_name: '',
  })
  const [loadingUsers, setLoadingUsers] = useState(false)
  const [usersError, setUsersError] = useState('')

  const canCreateUser = auth?.user?.is_admin === true
  const canDeleteUser = (userRoles: string[] | undefined) => {
    if (!auth?.user?.is_admin) return false
    const normalized = (userRoles || []).map((r) => r.toLowerCase().replace('_', ' ').trim())
    const targetIsSuper = normalized.includes('super admin')
    return auth.user.is_super_admin ? true : !targetIsSuper
  }

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

  useEffect(() => {
    const loadRoles = async () => {
      if (!auth?.accessToken || !auth?.user?.org_id) return
      try {
        const data = await apiRequest(`/roles?org_id=${auth.user.org_id}`, {
          method: 'GET',
          headers: { Authorization: `Bearer ${auth.accessToken}` },
        })
        setRoles(data || [])
      } catch {
        setRoles([])
      }
    }
    if (canCreateUser) {
      loadRoles()
    }
  }, [auth?.accessToken, auth?.user?.org_id, canCreateUser])

  const onCreateChange = (key: keyof typeof createForm) => (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setCreateForm((prev) => ({ ...prev, [key]: event.target.value }))
  }

  const onCreateUser = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!auth?.accessToken || !auth?.user?.org_id) return
    setCreateLoading(true)
    setCreateError('')
    try {
      await apiRequest('/users', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${auth.accessToken}`,
        },
        body: JSON.stringify({
          org_id: auth.user.org_id,
          email: createForm.email.trim(),
          display_name: createForm.display_name.trim(),
          phone: createForm.phone.trim(),
          status: createForm.status,
          role_name: createForm.role_name || undefined,
        }),
      })
      setShowCreate(false)
      setCreateForm({ email: '', display_name: '', phone: '', status: 'invited', role_name: '' })
      const data = await apiRequest(`/users?org_id=${auth.user.org_id}`, {
        method: 'GET',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      setUsers(data || [])
    } catch (err: any) {
      setCreateError(err.details?.detail || err.message)
    } finally {
      setCreateLoading(false)
    }
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
            <span className="logout-name">{displayName}</span>
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
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
                <div>
                  <h2>User Directory</h2>
                  <p className="helper">Manage users in your organization.</p>
                </div>
                {canCreateUser && (
                  <button className="button small" onClick={() => setShowCreate(true)}>
                    + User
                  </button>
                )}
              </div>
              {loadingUsers && <p className="helper">Loading users...</p>}
              {usersError && <p className="error">{usersError}</p>}
              {!loadingUsers && !usersError && (
                <div className="list">
                  {users.map((user) => (
                    <div key={user.id} className="list-item">
                      <div>
                        <strong>{user.display_name}</strong>
                        <div className="helper">{user.email}</div>
                        {user.roles && user.roles.length > 0 && (
                          <div className="role-tags">
                            {user.roles.map((role) => (
                              <span key={role} className="role-tag">{role}</span>
                            ))}
                          </div>
                        )}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span className={`status ${user.status}`}>{user.status}</span>
                        {canDeleteUser(user.roles) && (
                          <button
                            className="button secondary small"
                            onClick={async () => {
                              if (!auth?.accessToken || !auth?.user?.org_id) return
                              const ok = window.confirm(`Delete ${user.display_name}?`)
                              if (!ok) return
                              await apiRequest(`/users/${user.id}`, {
                                method: 'DELETE',
                                headers: {
                                  Authorization: `Bearer ${auth.accessToken}`,
                                },
                              })
                              const data = await apiRequest(`/users?org_id=${auth.user.org_id}`, {
                                method: 'GET',
                                headers: { Authorization: `Bearer ${auth.accessToken}` },
                              })
                              setUsers(data || [])
                            }}
                          >
                            Delete
                          </button>
                        )}
                      </div>
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
          {showCreate && (
            <div className="modal-backdrop" onClick={() => setShowCreate(false)}>
              <div className="modal" onClick={(e) => e.stopPropagation()}>
                <h3>Add User</h3>
                <form onSubmit={onCreateUser} style={{ display: 'grid', gap: '12px' }}>
                  <label>
                    Name
                    <input
                      className="input"
                      value={createForm.display_name}
                      onChange={onCreateChange('display_name')}
                      required
                    />
                  </label>
                  <label>
                    Email
                    <input
                      className="input"
                      type="email"
                      value={createForm.email}
                      onChange={onCreateChange('email')}
                      required
                    />
                  </label>
                  <label>
                    Phone
                    <input
                      className="input"
                      value={createForm.phone}
                      onChange={onCreateChange('phone')}
                    />
                  </label>
                  <label>
                    Status
                    <select className="input" value={createForm.status} onChange={onCreateChange('status')}>
                      <option value="invited">Invited</option>
                      <option value="active">Active</option>
                      <option value="suspended">Suspended</option>
                    </select>
                  </label>
                  <label>
                    Role
                    <select className="input" value={createForm.role_name} onChange={onCreateChange('role_name')}>
                      <option value="">Select role</option>
                      {roles.map((role) => (
                        <option key={role.id} value={role.name}>{role.name}</option>
                      ))}
                    </select>
                  </label>
                  {createError && <p className="error">{createError}</p>}
                  <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                    <button type="button" className="button secondary small" onClick={() => setShowCreate(false)}>
                      Cancel
                    </button>
                    <button className="button small" disabled={createLoading}>
                      {createLoading ? 'Creating...' : 'Create'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
