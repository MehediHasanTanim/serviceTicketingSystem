import { type ChangeEvent, type FormEvent, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/authContext'
import { apiRequest } from '../../shared/api/client'

export function HomePage() {
  const { auth, logout } = useAuth()
  const navigate = useNavigate()
  const [activeMenu, setActiveMenu] = useState<'dashboard' | 'users' | 'roles'>('users')
  const [users, setUsers] = useState<Array<{ id: number; display_name: string; email: string; phone?: string; status: string; roles?: string[] }>>([])
  const [showCreate, setShowCreate] = useState(false)
  const [showEdit, setShowEdit] = useState(false)
  const [editUserId, setEditUserId] = useState<number | null>(null)
  const [roles, setRoles] = useState<Array<{ id: number; name: string }>>([])
  const [roleList, setRoleList] = useState<Array<{ id: number; name: string; description: string }>>([])
  const [roleLoading, setRoleLoading] = useState(false)
  const [roleError, setRoleError] = useState('')
  const [showRoleModal, setShowRoleModal] = useState(false)
  const [roleEditingId, setRoleEditingId] = useState<number | null>(null)
  const [roleForm, setRoleForm] = useState({ name: '', description: '' })
  const [roleSaving, setRoleSaving] = useState(false)
  const [roleSearch, setRoleSearch] = useState('')
  const [rolePage, setRolePage] = useState(1)
  const [rolePageSize] = useState(10)
  const [roleTotal, setRoleTotal] = useState(0)
  const [roleSortBy, setRoleSortBy] = useState<'name' | 'created_at'>('name')
  const [roleSortDir, setRoleSortDir] = useState<'asc' | 'desc'>('asc')
  const [createError, setCreateError] = useState('')
  const [createLoading, setCreateLoading] = useState(false)
  const [inviteMessage, setInviteMessage] = useState('')
  const [editMessage, setEditMessage] = useState('')
  const [inviteLoadingId, setInviteLoadingId] = useState<number | null>(null)
  const [createForm, setCreateForm] = useState({
    email: '',
    display_name: '',
    phone: '',
    status: 'invited',
    role_name: '',
    password: '',
    confirm_password: '',
  })
  const [editForm, setEditForm] = useState({
    email: '',
    display_name: '',
    phone: '',
    status: 'active',
    role_name: '',
  })
  const [editError, setEditError] = useState('')
  const [editLoading, setEditLoading] = useState(false)
  const [loadingUsers, setLoadingUsers] = useState(false)
  const [usersError, setUsersError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [totalCount, setTotalCount] = useState(0)
  const [sortBy, setSortBy] = useState<'display_name' | 'email' | 'status'>('display_name')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

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

  const loadUsers = async (pageOverride?: number, queryOverride?: string) => {
    if (!auth?.accessToken || !auth?.user?.org_id) return
    setLoadingUsers(true)
    setUsersError('')
    try {
      const targetPage = pageOverride ?? page
      const targetQuery = (queryOverride ?? searchTerm).trim()
      const params = new URLSearchParams()
      params.set('org_id', String(auth.user.org_id))
      params.set('page', String(targetPage))
      params.set('page_size', String(pageSize))
      if (targetQuery) params.set('q', targetQuery)
      params.set('sort_by', sortBy)
      params.set('sort_dir', sortDir)
      const data = await apiRequest(`/users?${params.toString()}`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${auth.accessToken}`,
        },
      })
      const results = data?.results ?? data ?? []
      setUsers(results)
      setTotalCount(data?.count ?? results.length ?? 0)
    } catch (err: any) {
      setUsersError(err.details?.detail || err.message)
    } finally {
      setLoadingUsers(false)
    }
  }

  useEffect(() => {
    loadUsers()
  }, [auth?.accessToken, auth?.user?.org_id, page, pageSize, searchTerm, sortBy, sortDir])

  useEffect(() => {
    if (activeMenu === 'roles') {
      loadRoleList()
    }
  }, [activeMenu, auth?.accessToken, auth?.user?.org_id, rolePage, rolePageSize, roleSearch, roleSortBy, roleSortDir])

  useEffect(() => {
    const loadRoles = async () => {
      if (!auth?.accessToken || !auth?.user?.org_id) return
      try {
        const data = await apiRequest(`/roles?org_id=${auth.user.org_id}`, {
          method: 'GET',
          headers: { Authorization: `Bearer ${auth.accessToken}` },
        })
        setRoles(data || [])
        setRoleList(
          (data || []).map((role: any) => ({
            id: role.id,
            name: role.name,
            description: role.description || '',
          }))
        )
      } catch {
        setRoles([])
        setRoleList([])
      }
    }
    if (canCreateUser) {
      loadRoles()
    }
  }, [auth?.accessToken, auth?.user?.org_id, canCreateUser])

  const loadRoleList = async (pageOverride?: number, queryOverride?: string) => {
    if (!auth?.accessToken || !auth?.user?.org_id) return
    setRoleLoading(true)
    setRoleError('')
    try {
      const targetPage = pageOverride ?? rolePage
      const targetQuery = (queryOverride ?? roleSearch).trim()
      const params = new URLSearchParams()
      params.set('org_id', String(auth.user.org_id))
      params.set('page', String(targetPage))
      params.set('page_size', String(rolePageSize))
      params.set('sort_by', roleSortBy)
      params.set('sort_dir', roleSortDir)
      if (targetQuery) params.set('q', targetQuery)
      const data = await apiRequest(`/roles?${params.toString()}`, {
        method: 'GET',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      const results = data?.results ?? data ?? []
      setRoleList(
        (results || []).map((role: any) => ({
          id: role.id,
          name: role.name,
          description: role.description || '',
        }))
      )
      setRoleTotal(data?.count ?? results.length ?? 0)
    } catch (err: any) {
      setRoleError(err.details?.detail || err.message || 'Failed to load roles.')
    } finally {
      setRoleLoading(false)
    }
  }

  const onCreateChange = (key: keyof typeof createForm) => (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setCreateForm((prev) => ({ ...prev, [key]: event.target.value }))
  }

  const onCreateUser = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!auth?.accessToken || !auth?.user?.org_id) return
    setCreateLoading(true)
    setCreateError('')
    try {
      if (createForm.status === 'active') {
        if (!createForm.password || createForm.password.length < 8) {
          throw new Error('Password must be at least 8 characters for active users.')
        }
        if (createForm.password !== createForm.confirm_password) {
          throw new Error('Passwords do not match.')
        }
      }
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
          password: createForm.status === 'active' ? createForm.password : undefined,
        }),
      })
      setShowCreate(false)
      setCreateForm({ email: '', display_name: '', phone: '', status: 'invited', role_name: '', password: '', confirm_password: '' })
      await loadUsers(1)
    } catch (err: any) {
      setCreateError(err.details?.detail || err.message)
    } finally {
      setCreateLoading(false)
    }
  }

  const openEdit = (user: { id: number; email: string; display_name: string; phone?: string; status: string; roles?: string[] }) => {
    setEditUserId(user.id)
    setEditForm({
      email: user.email,
      display_name: user.display_name,
      phone: user.phone || '',
      status: user.status,
      role_name: (user.roles && user.roles[0]) || '',
    })
    setEditError('')
    setShowEdit(true)
  }

  const onEditChange = (key: keyof typeof editForm) => (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setEditForm((prev) => ({ ...prev, [key]: event.target.value }))
  }

  const onEditUser = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!auth?.accessToken || !auth?.user?.org_id || !editUserId) return
    setEditLoading(true)
    setEditError('')
    setEditMessage('')
    try {
      await apiRequest(`/users/${editUserId}`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${auth.accessToken}`,
        },
        body: JSON.stringify({
          email: editForm.email.trim(),
          display_name: editForm.display_name.trim(),
          phone: editForm.phone.trim(),
          status: editForm.status,
        }),
      })

      if (editForm.role_name) {
        await apiRequest(`/users/${editUserId}`, {
          method: 'PATCH',
          headers: {
            Authorization: `Bearer ${auth.accessToken}`,
          },
          body: JSON.stringify({
            role_name: editForm.role_name,
          }),
        })
      }

      await loadUsers(page)
      setShowEdit(false)
      setEditMessage('User updated successfully.')
      setTimeout(() => setEditMessage(''), 2000)
    } catch (err: any) {
      setEditError(err.details?.detail || err.message || 'Failed to update user.')
    } finally {
      setEditLoading(false)
    }
  }

  const openRoleModal = (role?: { id: number; name: string; description: string }) => {
    if (role) {
      setRoleEditingId(role.id)
      setRoleForm({ name: role.name, description: role.description || '' })
    } else {
      setRoleEditingId(null)
      setRoleForm({ name: '', description: '' })
    }
    setRoleError('')
    setShowRoleModal(true)
  }

  const onRoleChange = (key: keyof typeof roleForm) => (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setRoleForm((prev) => ({ ...prev, [key]: event.target.value }))
  }

  const onSaveRole = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!auth?.accessToken || !auth?.user?.org_id) return
    setRoleSaving(true)
    setRoleError('')
    try {
      if (roleEditingId) {
        await apiRequest(`/roles/${roleEditingId}`, {
          method: 'PATCH',
          headers: { Authorization: `Bearer ${auth.accessToken}` },
          body: JSON.stringify({
            name: roleForm.name.trim(),
            description: roleForm.description.trim(),
          }),
        })
      } else {
        await apiRequest('/roles', {
          method: 'POST',
          headers: { Authorization: `Bearer ${auth.accessToken}` },
          body: JSON.stringify({
            org_id: auth.user.org_id,
            name: roleForm.name.trim(),
            description: roleForm.description.trim(),
          }),
        })
      }
      setShowRoleModal(false)
      await loadRoleList(rolePage)
    } catch (err: any) {
      setRoleError(err.details?.detail || err.message || 'Failed to save role.')
    } finally {
      setRoleSaving(false)
    }
  }

  const onDeleteRole = async (roleId: number) => {
    if (!auth?.accessToken) return
    const ok = window.confirm('Delete this role?')
    if (!ok) return
    try {
      await apiRequest(`/roles/${roleId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      await loadRoleList()
    } catch (err: any) {
      setRoleError(err.details?.detail || err.message || 'Failed to delete role.')
    }
  }

  const resendInvite = async (userId: number) => {
    if (!auth?.accessToken || !auth?.user?.org_id) return
    setInviteMessage('')
    setUsersError('')
    setInviteLoadingId(userId)
    try {
      await apiRequest(`/users/${userId}/invite`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${auth.accessToken}`,
        },
      })
      await loadUsers(1)
      setInviteMessage('Invite has been resent.')
      setTimeout(() => setInviteMessage(''), 2000)
    } catch (err: any) {
      setUsersError(err.details?.detail || err.message || 'Failed to resend invite.')
    } finally {
      setInviteLoadingId(null)
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
      {(inviteMessage || editMessage) && <div className="toast">{inviteMessage || editMessage}</div>}
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
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <input
                    className="input"
                    placeholder="Search users"
                    value={searchTerm}
                    onChange={(event) => {
                      setPage(1)
                      setSearchTerm(event.target.value)
                    }}
                    style={{ minWidth: '220px' }}
                  />
                  <button
                    className="button secondary small"
                    onClick={() => loadUsers(1)}
                  >
                    Search
                  </button>
                  {canCreateUser && (
                    <button className="button primary small icon-button" onClick={() => setShowCreate(true)}>
                      <span className="icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                          <path d="M12 5v14M5 12h14" />
                        </svg>
                      </span>
                      Add User
                    </button>
                  )}
                </div>
              </div>
              {loadingUsers && <p className="helper">Loading users...</p>}
              {usersError && <p className="error">{usersError}</p>}
              {!loadingUsers && !usersError && (
                <div className="list">
                  <div className="list-header">
                    <button
                      className="header-button"
                      onClick={() => {
                        if (sortBy === 'display_name') {
                          setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
                        } else {
                          setSortBy('display_name')
                          setSortDir('asc')
                        }
                      }}
                    >
                      Name
                      {sortBy === 'display_name' && <span className="sort-indicator">{sortDir === 'asc' ? '▲' : '▼'}</span>}
                    </button>
                    <button
                      className="header-button"
                      onClick={() => {
                        if (sortBy === 'email') {
                          setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
                        } else {
                          setSortBy('email')
                          setSortDir('asc')
                        }
                      }}
                    >
                      Email
                      {sortBy === 'email' && <span className="sort-indicator">{sortDir === 'asc' ? '▲' : '▼'}</span>}
                    </button>
                    <span>Role</span>
                    <button
                      className="header-button"
                      onClick={() => {
                        if (sortBy === 'status') {
                          setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
                        } else {
                          setSortBy('status')
                          setSortDir('asc')
                        }
                      }}
                    >
                      Status
                      {sortBy === 'status' && <span className="sort-indicator">{sortDir === 'asc' ? '▲' : '▼'}</span>}
                    </button>
                    <span>Actions</span>
                  </div>
                  {users.map((user) => (
                    <div key={user.id} className="list-item">
                      <div className="cell name">
                        <strong>{user.display_name}</strong>
                      </div>
                      <div className="cell email">{user.email}</div>
                      <div className="cell role">
                        {user.roles && user.roles.length > 0 ? user.roles.join(', ') : '-'}
                      </div>
                      <div className="cell status-cell">
                        <span className={`status ${user.status}`}>{user.status}</span>
                      </div>
                      <div className="cell actions">
                        {canCreateUser && (
                          <button className="button secondary small" onClick={() => openEdit(user)}>
                            Edit
                          </button>
                        )}
                        {canCreateUser && user.status === 'invited' && (
                          <button
                            className="button secondary small"
                            onClick={() => resendInvite(user.id)}
                            disabled={inviteLoadingId === user.id}
                          >
                            {inviteLoadingId === user.id ? 'Resending...' : 'Resend Invite'}
                          </button>
                        )}
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
                              await loadUsers(page)
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
              {!loadingUsers && !usersError && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
                  <span className="helper">
                    Showing {users.length === 0 ? 0 : (page - 1) * pageSize + 1}-
                    {(page - 1) * pageSize + users.length} of {totalCount}
                  </span>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      className="button secondary small"
                      onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
                      disabled={page <= 1}
                    >
                      Prev
                    </button>
                    <button
                      className="button secondary small"
                      onClick={() => setPage((prev) => prev + 1)}
                      disabled={page * pageSize >= totalCount}
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
          {activeMenu === 'roles' && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
                <div>
                  <h2>Role Management</h2>
                  <p className="helper">Create and manage roles.</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <input
                    className="input"
                    placeholder="Search roles"
                    value={roleSearch}
                    onChange={(event) => {
                      setRolePage(1)
                      setRoleSearch(event.target.value)
                    }}
                    style={{ minWidth: '220px' }}
                  />
                  <button className="button secondary small" onClick={() => loadRoleList(1)}>
                    Search
                  </button>
                  {canCreateUser && (
                    <button className="button primary small icon-button" onClick={() => openRoleModal()}>
                      <span className="icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                          <path d="M12 5v14M5 12h14" />
                        </svg>
                      </span>
                      Add Role
                    </button>
                  )}
                </div>
              </div>
              {roleLoading && <p className="helper">Loading roles...</p>}
              {roleError && <p className="error">{roleError}</p>}
              {!roleLoading && !roleError && (
                <div className="list">
                  <div className="list-header">
                    <button
                      className="header-button"
                      onClick={() => {
                        if (roleSortBy === 'name') {
                          setRoleSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
                        } else {
                          setRoleSortBy('name')
                          setRoleSortDir('asc')
                        }
                      }}
                    >
                      Name
                      {roleSortBy === 'name' && <span className="sort-indicator">{roleSortDir === 'asc' ? '▲' : '▼'}</span>}
                    </button>
                    <span>Description</span>
                    <button
                      className="header-button"
                      onClick={() => {
                        if (roleSortBy === 'created_at') {
                          setRoleSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
                        } else {
                          setRoleSortBy('created_at')
                          setRoleSortDir('asc')
                        }
                      }}
                    >
                      Created
                      {roleSortBy === 'created_at' && <span className="sort-indicator">{roleSortDir === 'asc' ? '▲' : '▼'}</span>}
                    </button>
                    <span>Actions</span>
                  </div>
                  {roleList.map((role) => (
                    <div key={role.id} className="list-item role-row">
                      <div className="cell">{role.name}</div>
                      <div className="cell">{role.description || '-'}</div>
                      <div className="cell">{role.created_at ? new Date(role.created_at).toLocaleDateString() : '-'}</div>
                      <div className="cell actions">
                        <button className="button secondary small" onClick={() => openRoleModal(role)}>
                          Edit
                        </button>
                        <button className="button secondary small" onClick={() => onDeleteRole(role.id)}>
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {!roleLoading && !roleError && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
                  <span className="helper">
                    Showing {roleList.length === 0 ? 0 : (rolePage - 1) * rolePageSize + 1}-
                    {(rolePage - 1) * rolePageSize + roleList.length} of {roleTotal}
                  </span>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      className="button secondary small"
                      onClick={() => setRolePage((prev) => Math.max(prev - 1, 1))}
                      disabled={rolePage <= 1}
                    >
                      Prev
                    </button>
                    <button
                      className="button secondary small"
                      onClick={() => setRolePage((prev) => prev + 1)}
                      disabled={rolePage * rolePageSize >= roleTotal}
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
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
                  {createForm.status === 'active' && (
                    <>
                      <label>
                        Password
                        <input
                          className="input"
                          type="password"
                          value={createForm.password}
                          onChange={onCreateChange('password')}
                          required
                        />
                      </label>
                      <label>
                        Confirm Password
                        <input
                          className="input"
                          type="password"
                          value={createForm.confirm_password}
                          onChange={onCreateChange('confirm_password')}
                          required
                        />
                      </label>
                    </>
                  )}
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
          {showEdit && (
            <div className="modal-backdrop" onClick={() => setShowEdit(false)}>
              <div className="modal" onClick={(e) => e.stopPropagation()}>
                <h3>Edit User</h3>
                <form onSubmit={onEditUser} style={{ display: 'grid', gap: '12px' }}>
                  <label>
                    Name
                    <input
                      className="input"
                      value={editForm.display_name}
                      onChange={onEditChange('display_name')}
                      required
                    />
                  </label>
                  <label>
                    Email
                    <input
                      className="input"
                      type="email"
                      value={editForm.email}
                      onChange={onEditChange('email')}
                      required
                    />
                  </label>
                  <label>
                    Phone
                    <input
                      className="input"
                      value={editForm.phone}
                      onChange={onEditChange('phone')}
                    />
                  </label>
                  <label>
                    Status
                    <select className="input" value={editForm.status} onChange={onEditChange('status')}>
                      <option value="invited">Invited</option>
                      <option value="active">Active</option>
                      <option value="suspended">Suspended</option>
                    </select>
                  </label>
                  <label>
                    Role
                    <select className="input" value={editForm.role_name} onChange={onEditChange('role_name')}>
                      <option value="">Select role</option>
                      {roles.map((role) => (
                        <option key={role.id} value={role.name}>{role.name}</option>
                      ))}
                    </select>
                  </label>
                  {editError && <p className="error">{editError}</p>}
                  <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                    <button type="button" className="button secondary small" onClick={() => setShowEdit(false)}>
                      Cancel
                    </button>
                    <button className="button small" disabled={editLoading}>
                      {editLoading ? 'Saving...' : 'Save'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
          {showRoleModal && (
            <div className="modal-backdrop" onClick={() => setShowRoleModal(false)}>
              <div className="modal" onClick={(e) => e.stopPropagation()}>
                <h3>{roleEditingId ? 'Edit Role' : 'Add Role'}</h3>
                <form onSubmit={onSaveRole} style={{ display: 'grid', gap: '12px' }}>
                  <label>
                    Name
                    <input
                      className="input"
                      value={roleForm.name}
                      onChange={onRoleChange('name')}
                      required
                    />
                  </label>
                  <label>
                    Description
                    <textarea
                      className="input"
                      rows={3}
                      value={roleForm.description}
                      onChange={onRoleChange('description')}
                    />
                  </label>
                  {roleError && <p className="error">{roleError}</p>}
                  <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                    <button type="button" className="button secondary small" onClick={() => setShowRoleModal(false)}>
                      Cancel
                    </button>
                    <button className="button small" disabled={roleSaving}>
                      {roleSaving ? 'Saving...' : 'Save'}
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
