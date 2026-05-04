import { type ChangeEvent, type FormEvent, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/authContext'
import { apiRequest } from '../../shared/api/client'

const TIMEZONE_OPTIONS = (() => {
  const fallback = [
    'UTC',
    'America/New_York',
    'America/Chicago',
    'America/Denver',
    'America/Los_Angeles',
    'America/Phoenix',
    'America/Anchorage',
    'Pacific/Honolulu',
    'Europe/London',
    'Europe/Paris',
    'Europe/Berlin',
    'Asia/Dubai',
    'Asia/Dhaka',
    'Asia/Kolkata',
    'Asia/Singapore',
    'Asia/Tokyo',
    'Australia/Sydney',
  ]
  try {
    const supported = (Intl as any)?.supportedValuesOf?.('timeZone')
    if (Array.isArray(supported) && supported.length > 0) {
      return supported
    }
  } catch {
    // ignore
  }
  return fallback
})()

const COUNTRY_OPTIONS = [
  'United States',
  'Canada',
  'United Kingdom',
  'France',
  'Germany',
  'Spain',
  'Italy',
  'Netherlands',
  'Switzerland',
  'Sweden',
  'Norway',
  'Denmark',
  'Ireland',
  'Portugal',
  'Turkey',
  'United Arab Emirates',
  'Saudi Arabia',
  'Qatar',
  'Kuwait',
  'Oman',
  'Bahrain',
  'India',
  'Bangladesh',
  'Pakistan',
  'Sri Lanka',
  'Nepal',
  'China',
  'Japan',
  'South Korea',
  'Singapore',
  'Malaysia',
  'Thailand',
  'Vietnam',
  'Indonesia',
  'Philippines',
  'Australia',
  'New Zealand',
  'South Africa',
  'Egypt',
  'Kenya',
  'Nigeria',
  'Brazil',
  'Mexico',
  'Argentina',
  'Chile',
  'Colombia',
]

export function HomePage() {
  const { auth, logout } = useAuth()
  const navigate = useNavigate()
  const [activeMenu, setActiveMenu] = useState<'dashboard' | 'users' | 'roles' | 'permissions' | 'orgs' | 'properties' | 'departments' | 'audit'>('users')
  const [users, setUsers] = useState<Array<{ id: number; display_name: string; email: string; phone?: string; status: string; roles?: string[] }>>([])
  const [showCreate, setShowCreate] = useState(false)
  const [showEdit, setShowEdit] = useState(false)
  const [editUserId, setEditUserId] = useState<number | null>(null)
  const [roles, setRoles] = useState<Array<{ id: number; name: string }>>([])
  const [roleList, setRoleList] = useState<Array<{ id: number; name: string; description: string; created_at?: string }>>([])
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
  const [permissionList, setPermissionList] = useState<Array<{ id: number; code: string; description: string }>>([])
  const [permissionLoading, setPermissionLoading] = useState(false)
  const [permissionError, setPermissionError] = useState('')
  const [showPermissionModal, setShowPermissionModal] = useState(false)
  const [permissionEditingId, setPermissionEditingId] = useState<number | null>(null)
  const [permissionForm, setPermissionForm] = useState({ code: '', description: '' })
  const [permissionSaving, setPermissionSaving] = useState(false)
  const [permissionSearch, setPermissionSearch] = useState('')
  const [permissionPage, setPermissionPage] = useState(1)
  const [permissionPageSize] = useState(10)
  const [permissionTotal, setPermissionTotal] = useState(0)
  const [permissionSortBy, setPermissionSortBy] = useState<'code' | 'id'>('code')
  const [permissionSortDir, setPermissionSortDir] = useState<'asc' | 'desc'>('asc')
  const [rolePermissionAssignments, setRolePermissionAssignments] = useState<Array<{ permission_id: number; code: string; description: string }>>([])
  const [rolePermissionLoading, setRolePermissionLoading] = useState(false)
  const [rolePermissionError, setRolePermissionError] = useState('')
  const [showRolePermissions, setShowRolePermissions] = useState(false)
  const [activeRoleId, setActiveRoleId] = useState<number | null>(null)
  const [activeRoleName, setActiveRoleName] = useState('')
  const [orgList, setOrgList] = useState<Array<{ id: number; name: string; legal_name: string; status: string }>>([])
  const [orgLoading, setOrgLoading] = useState(false)
  const [orgError, setOrgError] = useState('')
  const [orgSearch, setOrgSearch] = useState('')
  const [orgPage, setOrgPage] = useState(1)
  const [orgPageSize] = useState(10)
  const [orgTotal, setOrgTotal] = useState(0)
  const [orgSortBy, setOrgSortBy] = useState<'id' | 'name' | 'legal_name' | 'status' | 'created_at'>('id')
  const [orgSortDir, setOrgSortDir] = useState<'asc' | 'desc'>('asc')
  const [showOrgModal, setShowOrgModal] = useState(false)
  const [orgEditingId, setOrgEditingId] = useState<number | null>(null)
  const [orgForm, setOrgForm] = useState({ name: '', legal_name: '', status: 'active' })
  const [orgSaving, setOrgSaving] = useState(false)
  const [propertyList, setPropertyList] = useState<Array<{
    id: number
    org_id: number
    code: string
    name: string
    timezone: string
    city: string
    country: string
  }>>([])
  const [propertyLoading, setPropertyLoading] = useState(false)
  const [propertyError, setPropertyError] = useState('')
  const [propertySearch, setPropertySearch] = useState('')
  const [propertyPage, setPropertyPage] = useState(1)
  const [propertyPageSize] = useState(10)
  const [propertyTotal, setPropertyTotal] = useState(0)
  const [propertySortBy, setPropertySortBy] = useState<'code' | 'name' | 'city' | 'country'>('name')
  const [propertySortDir, setPropertySortDir] = useState<'asc' | 'desc'>('asc')
  const [showPropertyModal, setShowPropertyModal] = useState(false)
  const [propertyEditingId, setPropertyEditingId] = useState<number | null>(null)
  const [propertyForm, setPropertyForm] = useState({
    code: '',
    name: '',
    timezone: '',
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    postal_code: '',
    country: '',
  })
  const [propertySaving, setPropertySaving] = useState(false)
  const [departmentList, setDepartmentList] = useState<Array<{
    id: number
    org_id: number
    property_id?: number | null
    name: string
    description: string
    created_at?: string
  }>>([])
  const [departmentAssignments, setDepartmentAssignments] = useState<Array<{
    department_id: number
    name: string
    property_id?: number | null
    is_primary?: boolean
  }>>([])
  const [departmentAssignUserId, setDepartmentAssignUserId] = useState<number | null>(null)
  const [departmentAssignUserName, setDepartmentAssignUserName] = useState('')
  const [showDepartmentAssign, setShowDepartmentAssign] = useState(false)
  const [departmentAssignLoading, setDepartmentAssignLoading] = useState(false)
  const [departmentAssignError, setDepartmentAssignError] = useState('')
  const [userRoleAssignments, setUserRoleAssignments] = useState<Array<{ role_id: number; name: string }>>([])
  const [userRoleLoading, setUserRoleLoading] = useState(false)
  const [userRoleError, setUserRoleError] = useState('')
  const [showUserRoles, setShowUserRoles] = useState(false)
  const [roleAssignUserId, setRoleAssignUserId] = useState<number | null>(null)
  const [roleAssignUserName, setRoleAssignUserName] = useState('')
  const [departmentLoading, setDepartmentLoading] = useState(false)
  const [departmentError, setDepartmentError] = useState('')
  const [showDepartmentModal, setShowDepartmentModal] = useState(false)
  const [departmentEditingId, setDepartmentEditingId] = useState<number | null>(null)
  const [departmentForm, setDepartmentForm] = useState({
    property_id: '',
    name: '',
    description: '',
  })
  const [departmentSaving, setDepartmentSaving] = useState(false)
  const [departmentSearch, setDepartmentSearch] = useState('')
  const [departmentPage, setDepartmentPage] = useState(1)
  const [departmentPageSize] = useState(10)
  const [departmentTotal, setDepartmentTotal] = useState(0)
  const [departmentSortBy, setDepartmentSortBy] = useState<'name' | 'created_at'>('name')
  const [departmentSortDir, setDepartmentSortDir] = useState<'asc' | 'desc'>('asc')
  const [auditLogs, setAuditLogs] = useState<Array<{
    id: number
    org_id: number
    property_id?: number | null
    actor_user_id?: number | null
    action: string
    target_type: string
    target_id: string
    metadata?: Record<string, unknown>
    ip_address: string
    user_agent: string
    created_at: string
  }>>([])
  const [auditLoading, setAuditLoading] = useState(false)
  const [auditError, setAuditError] = useState('')
  const [auditSearch, setAuditSearch] = useState('')
  const [auditActor, setAuditActor] = useState('')
  const [auditAction, setAuditAction] = useState('')
  const [auditTargetType, setAuditTargetType] = useState('')
  const [auditDateFrom, setAuditDateFrom] = useState('')
  const [auditDateTo, setAuditDateTo] = useState('')
  const [auditPage, setAuditPage] = useState(1)
  const [auditPageSize] = useState(10)
  const [auditTotal, setAuditTotal] = useState(0)
  const [auditSortBy, setAuditSortBy] = useState<'created_at' | 'action' | 'target_type'>('created_at')
  const [auditSortDir, setAuditSortDir] = useState<'asc' | 'desc'>('desc')
  const [showPropertyAssign, setShowPropertyAssign] = useState(false)
  const [assignUserId, setAssignUserId] = useState<number | null>(null)
  const [assignUserName, setAssignUserName] = useState('')
  const [assignmentLoading, setAssignmentLoading] = useState(false)
  const [assignmentError, setAssignmentError] = useState('')
  const [assignedProperties, setAssignedProperties] = useState<Array<{
    property_id: number
    code: string
    name: string
    is_primary: boolean
  }>>([])
  const [createError, setCreateError] = useState('')
  const [createLoading, setCreateLoading] = useState(false)
  const [inviteMessage, setInviteMessage] = useState('')
  const [editMessage, setEditMessage] = useState('')
  const [inviteLoadingId, setInviteLoadingId] = useState<number | null>(null)
  const [orgName, setOrgName] = useState('')
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
  const [editRoleIds, setEditRoleIds] = useState<number[]>([])
  const [editRoleIdsInitial, setEditRoleIdsInitial] = useState<number[]>([])
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

  const permissions = auth?.user?.permissions || []
  const hasPermission = (code: string) => auth?.user?.is_super_admin || permissions.includes(code)
  const canViewUsers = hasPermission('users.view') || hasPermission('users.manage')
  const canManageUsers = hasPermission('users.manage')
  const canViewRoles = hasPermission('roles.view') || hasPermission('roles.manage')
  const canManageRoles = hasPermission('roles.manage')
  const canViewPermissions = hasPermission('permissions.view') || hasPermission('permissions.manage')
  const canManagePermissions = hasPermission('permissions.manage')
  const canViewOrgs = hasPermission('org.view') || hasPermission('org.manage')
  const canManageOrgs = hasPermission('org.manage')
  const canViewProperties = hasPermission('properties.view') || hasPermission('properties.manage')
  const canManageProperties = hasPermission('properties.manage')
  const canViewDepartments = hasPermission('departments.view') || hasPermission('departments.manage')
  const canManageDepartments = hasPermission('departments.manage')
  const canViewAudit = hasPermission('audit.view') || hasPermission('audit.manage')
  const canDeleteUser = (userRoles: string[] | undefined) => {
    if (!canManageUsers) return false
    const normalized = (userRoles || []).map((r) => r.toLowerCase().replace('_', ' ').trim())
    const targetIsSuper = normalized.includes('super admin')
    return auth?.user?.is_super_admin ? true : !targetIsSuper
  }

  const onSignOut = async () => {
    await logout()
    navigate('/login')
  }

  const loadUserPropertyAssignments = async (userId: number) => {
    if (!auth?.accessToken) return
    setAssignmentLoading(true)
    setAssignmentError('')
    try {
      const data = await apiRequest(`/users/${userId}/properties`, {
        method: 'GET',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      setAssignedProperties(data || [])
    } catch (err: any) {
      setAssignmentError(err.details?.detail || err.message || 'Failed to load assignments.')
    } finally {
      setAssignmentLoading(false)
    }
  }

  const openPropertyAssignments = async (user: { id: number; display_name: string }) => {
    setAssignUserId(user.id)
    setAssignUserName(user.display_name)
    setAssignedProperties([])
    setAssignmentError('')
    setShowPropertyAssign(true)
    if (propertyList.length === 0) {
      await loadPropertyList()
    }
    await loadUserPropertyAssignments(user.id)
  }

  const isAssigned = (propertyId: number) =>
    assignedProperties.some((assignment) => assignment.property_id === propertyId)
  const primaryPropertyId = assignedProperties.find((assignment) => assignment.is_primary)?.property_id ?? null

  const onAssignProperty = async (propertyId: number, makePrimary = false) => {
    if (!auth?.accessToken || !assignUserId) return
    setAssignmentLoading(true)
    setAssignmentError('')
    try {
      await apiRequest(`/users/${assignUserId}/properties`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
        body: JSON.stringify({ property_id: propertyId, is_primary: makePrimary }),
      })
      await loadUserPropertyAssignments(assignUserId)
    } catch (err: any) {
      setAssignmentError(err.details?.detail || err.message || 'Failed to assign property.')
    } finally {
      setAssignmentLoading(false)
    }
  }

  const onUnassignProperty = async (propertyId: number) => {
    if (!auth?.accessToken || !assignUserId) return
    setAssignmentLoading(true)
    setAssignmentError('')
    try {
      await apiRequest(`/users/${assignUserId}/properties/${propertyId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      await loadUserPropertyAssignments(assignUserId)
    } catch (err: any) {
      setAssignmentError(err.details?.detail || err.message || 'Failed to unassign property.')
    } finally {
      setAssignmentLoading(false)
    }
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
    if (activeMenu === 'permissions') {
      loadPermissionList()
    }
  }, [activeMenu, auth?.accessToken, permissionPage, permissionPageSize, permissionSearch, permissionSortBy, permissionSortDir])

  useEffect(() => {
    if (activeMenu === 'orgs') {
      loadOrgList()
    }
  }, [activeMenu, auth?.accessToken, orgPage, orgPageSize, orgSearch, orgSortBy, orgSortDir])

  useEffect(() => {
    if (activeMenu === 'properties') {
      loadPropertyList()
    }
  }, [activeMenu, auth?.accessToken, auth?.user?.org_id, propertyPage, propertyPageSize, propertySearch, propertySortBy, propertySortDir])

  useEffect(() => {
    if (activeMenu === 'departments') {
      loadDepartmentList()
      if (propertyList.length === 0) {
        loadPropertyList()
      }
    }
  }, [activeMenu, auth?.accessToken, auth?.user?.org_id, departmentPage, departmentPageSize, departmentSearch, departmentSortBy, departmentSortDir])

  useEffect(() => {
    if (activeMenu === 'audit') {
      loadAuditLogs()
    }
  }, [
    activeMenu,
    auth?.accessToken,
    auth?.user?.org_id,
    auditPage,
    auditPageSize,
    auditSearch,
    auditSortBy,
    auditSortDir,
    auditActor,
    auditAction,
    auditTargetType,
    auditDateFrom,
    auditDateTo,
  ])

  useEffect(() => {
    const loadRoles = async () => {
      if (!auth?.accessToken || !auth?.user?.org_id) return
      try {
        const data = await apiRequest(`/roles?org_id=${auth.user.org_id}&page=1&page_size=200`, {
          method: 'GET',
          headers: { Authorization: `Bearer ${auth.accessToken}` },
        })
        const results = data?.results ?? data ?? []
        setRoles(results || [])
        setRoleList(
          (results || []).map((role: any) => ({
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
    if (canManageUsers) {
      loadRoles()
    }
  }, [auth?.accessToken, auth?.user?.org_id, canManageUsers])

  useEffect(() => {
    const loadPermissions = async () => {
      if (!auth?.accessToken) return
      try {
        const data = await apiRequest('/permissions?page=1&page_size=200', {
          method: 'GET',
          headers: { Authorization: `Bearer ${auth.accessToken}` },
        })
        setPermissionList(data?.results ?? data ?? [])
      } catch {
        setPermissionList([])
      }
    }
    if (canManageRoles) {
      loadPermissions()
    }
  }, [auth?.accessToken, canManageRoles])

  const loadPermissionList = async (pageOverride?: number, queryOverride?: string) => {
    if (!auth?.accessToken) return
    setPermissionLoading(true)
    setPermissionError('')
    try {
      const targetPage = pageOverride ?? permissionPage
      const targetQuery = (queryOverride ?? permissionSearch).trim()
      const params = new URLSearchParams()
      params.set('page', String(targetPage))
      params.set('page_size', String(permissionPageSize))
      params.set('sort_by', permissionSortBy)
      params.set('sort_dir', permissionSortDir)
      if (targetQuery) params.set('q', targetQuery)
      const data = await apiRequest(`/permissions?${params.toString()}`, {
        method: 'GET',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      const results = data?.results ?? data ?? []
      setPermissionList(results)
      setPermissionTotal(data?.count ?? results.length ?? 0)
    } catch (err: any) {
      setPermissionError(err.details?.detail || err.message || 'Failed to load permissions.')
    } finally {
      setPermissionLoading(false)
    }
  }

  const openPermissionModal = (perm?: any) => {
    if (perm) {
      setPermissionEditingId(perm.id)
      setPermissionForm({
        code: perm.code,
        description: perm.description || '',
      })
    } else {
      setPermissionEditingId(null)
      setPermissionForm({ code: '', description: '' })
    }
    setPermissionError('')
    setShowPermissionModal(true)
  }

  const onPermissionChange = (key: keyof typeof permissionForm) =>
    (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      setPermissionForm((prev) => ({ ...prev, [key]: event.target.value }))
    }

  const onSavePermission = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!auth?.accessToken) return
    setPermissionSaving(true)
    setPermissionError('')
    try {
      if (permissionEditingId) {
        await apiRequest(`/permissions/${permissionEditingId}`, {
          method: 'PATCH',
          headers: { Authorization: `Bearer ${auth.accessToken}` },
          body: JSON.stringify({
            code: permissionForm.code.trim(),
            description: permissionForm.description.trim(),
          }),
        })
      } else {
        await apiRequest('/permissions', {
          method: 'POST',
          headers: { Authorization: `Bearer ${auth.accessToken}` },
          body: JSON.stringify({
            code: permissionForm.code.trim(),
            description: permissionForm.description.trim(),
          }),
        })
      }
      setShowPermissionModal(false)
      await loadPermissionList()
    } catch (err: any) {
      setPermissionError(err.details?.detail || err.message || 'Failed to save permission.')
    } finally {
      setPermissionSaving(false)
    }
  }

  const onDeletePermission = async (permId: number) => {
    if (!auth?.accessToken) return
    const ok = window.confirm('Delete this permission?')
    if (!ok) return
    try {
      await apiRequest(`/permissions/${permId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      await loadPermissionList()
    } catch (err: any) {
      setPermissionError(err.details?.detail || err.message || 'Failed to delete permission.')
    }
  }

  const loadRolePermissions = async (roleId: number) => {
    if (!auth?.accessToken) return
    setRolePermissionLoading(true)
    setRolePermissionError('')
    try {
      const data = await apiRequest(`/roles/${roleId}/permissions`, {
        method: 'GET',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      setRolePermissionAssignments(data || [])
    } catch (err: any) {
      setRolePermissionError(err.details?.detail || err.message || 'Failed to load role permissions.')
    } finally {
      setRolePermissionLoading(false)
    }
  }

  const openRolePermissions = async (role: { id: number; name: string }) => {
    setActiveRoleId(role.id)
    setActiveRoleName(role.name)
    setRolePermissionAssignments([])
    setRolePermissionError('')
    setShowRolePermissions(true)
    if (permissionList.length === 0) {
      await loadPermissionList(1)
    }
    await loadRolePermissions(role.id)
  }

  const isPermissionAssigned = (permissionId: number) =>
    rolePermissionAssignments.some((assignment) => assignment.permission_id === permissionId)

  const onAssignPermission = async (permissionId: number) => {
    if (!auth?.accessToken || !activeRoleId) return
    setRolePermissionLoading(true)
    setRolePermissionError('')
    try {
      await apiRequest(`/roles/${activeRoleId}/permissions`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
        body: JSON.stringify({ permission_id: permissionId }),
      })
      await loadRolePermissions(activeRoleId)
    } catch (err: any) {
      setRolePermissionError(err.details?.detail || err.message || 'Failed to assign permission.')
    } finally {
      setRolePermissionLoading(false)
    }
  }

  const onUnassignPermission = async (permissionId: number) => {
    if (!auth?.accessToken || !activeRoleId) return
    setRolePermissionLoading(true)
    setRolePermissionError('')
    try {
      await apiRequest(`/roles/${activeRoleId}/permissions/${permissionId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      await loadRolePermissions(activeRoleId)
    } catch (err: any) {
      setRolePermissionError(err.details?.detail || err.message || 'Failed to unassign permission.')
    } finally {
      setRolePermissionLoading(false)
    }
  }

  useEffect(() => {
    const loadOrgName = async () => {
      if (!auth?.accessToken || !auth?.user?.org_id) return
      try {
        const data = await apiRequest(`/organizations/${auth.user.org_id}`, {
          method: 'GET',
          headers: { Authorization: `Bearer ${auth.accessToken}` },
        })
        setOrgName(data?.name || '')
      } catch {
        setOrgName('')
      }
    }
    loadOrgName()
  }, [auth?.accessToken, auth?.user?.org_id])

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
    const roleNames = new Set((user.roles || []).map((r) => r.toLowerCase()))
    const roleIds = roles
      .filter((role) => roleNames.has(role.name.toLowerCase()))
      .map((role) => role.id)
    setEditUserId(user.id)
    setEditForm({
      email: user.email,
      display_name: user.display_name,
      phone: user.phone || '',
      status: user.status,
      role_name: (user.roles && user.roles[0]) || '',
    })
    setEditRoleIds(roleIds)
    setEditRoleIdsInitial(roleIds)
    setEditError('')
    setShowEdit(true)
  }

  const onEditChange = (key: keyof typeof editForm) => (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setEditForm((prev) => ({ ...prev, [key]: event.target.value }))
  }

  const onEditRoleToggle = (roleId: number, checked: boolean) => {
    setEditRoleIds((prev) => {
      if (checked) {
        return prev.includes(roleId) ? prev : [...prev, roleId]
      }
      return prev.filter((id) => id !== roleId)
    })
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

      const toAdd = editRoleIds.filter((id) => !editRoleIdsInitial.includes(id))
      const toRemove = editRoleIdsInitial.filter((id) => !editRoleIds.includes(id))
      for (const roleId of toAdd) {
        await apiRequest(`/users/${editUserId}/roles`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${auth.accessToken}`,
          },
          body: JSON.stringify({ role_id: roleId }),
        })
      }
      for (const roleId of toRemove) {
        await apiRequest(`/users/${editUserId}/roles/${roleId}`, {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${auth.accessToken}`,
          },
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

  const loadOrgList = async () => {
    if (!auth?.accessToken) return
    setOrgLoading(true)
    setOrgError('')
    try {
      const params = new URLSearchParams()
      params.set('page', String(orgPage))
      params.set('page_size', String(orgPageSize))
      params.set('sort_by', orgSortBy)
      params.set('sort_dir', orgSortDir)
      if (orgSearch.trim()) params.set('q', orgSearch.trim())
      const data = await apiRequest(`/organizations?${params.toString()}`, {
        method: 'GET',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      const results = data?.results ?? data ?? []
      setOrgList(results)
      setOrgTotal(data?.count ?? results.length ?? 0)
    } catch (err: any) {
      setOrgError(err.details?.detail || err.message || 'Failed to load organizations.')
    } finally {
      setOrgLoading(false)
    }
  }

  const openOrgModal = (org?: { id: number; name: string; legal_name: string; status: string }) => {
    if (org) {
      setOrgEditingId(org.id)
      setOrgForm({ name: org.name, legal_name: org.legal_name, status: org.status })
    } else {
      setOrgEditingId(null)
      setOrgForm({ name: '', legal_name: '', status: 'active' })
    }
    setOrgError('')
    setShowOrgModal(true)
  }

  const onOrgChange = (key: keyof typeof orgForm) => (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setOrgForm((prev) => ({ ...prev, [key]: event.target.value }))
  }

  const onSaveOrg = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!auth?.accessToken) return
    setOrgSaving(true)
    setOrgError('')
    try {
      if (orgEditingId) {
        await apiRequest(`/organizations/${orgEditingId}`, {
          method: 'PATCH',
          headers: { Authorization: `Bearer ${auth.accessToken}` },
          body: JSON.stringify({
            name: orgForm.name.trim(),
            legal_name: orgForm.legal_name.trim(),
            status: orgForm.status,
          }),
        })
      } else {
        await apiRequest('/organizations', {
          method: 'POST',
          headers: { Authorization: `Bearer ${auth.accessToken}` },
          body: JSON.stringify({
            name: orgForm.name.trim(),
            legal_name: orgForm.legal_name.trim(),
            status: orgForm.status,
          }),
        })
      }
      setShowOrgModal(false)
      await loadOrgList()
    } catch (err: any) {
      setOrgError(err.details?.detail || err.message || 'Failed to save organization.')
    } finally {
      setOrgSaving(false)
    }
  }

  const onDeleteOrg = async (orgId: number) => {
    if (!auth?.accessToken) return
    const ok = window.confirm('Delete this organization?')
    if (!ok) return
    try {
      await apiRequest(`/organizations/${orgId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      await loadOrgList()
    } catch (err: any) {
      setOrgError(err.details?.detail || err.message || 'Failed to delete organization.')
    }
  }

  const loadPropertyList = async (pageOverride?: number, queryOverride?: string) => {
    if (!auth?.accessToken || !auth?.user?.org_id) return
    setPropertyLoading(true)
    setPropertyError('')
    try {
      const targetPage = pageOverride ?? propertyPage
      const targetQuery = (queryOverride ?? propertySearch).trim()
      const params = new URLSearchParams()
      params.set('org_id', String(auth.user.org_id))
      params.set('page', String(targetPage))
      params.set('page_size', String(propertyPageSize))
      params.set('sort_by', propertySortBy)
      params.set('sort_dir', propertySortDir)
      if (targetQuery) params.set('q', targetQuery)
      const data = await apiRequest(`/properties?${params.toString()}`, {
        method: 'GET',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      const results = data?.results ?? data ?? []
      setPropertyList(results)
      setPropertyTotal(data?.count ?? results.length ?? 0)
    } catch (err: any) {
      setPropertyError(err.details?.detail || err.message || 'Failed to load properties.')
    } finally {
      setPropertyLoading(false)
    }
  }

  const loadDepartmentList = async (pageOverride?: number, queryOverride?: string) => {
    if (!auth?.accessToken || !auth?.user?.org_id) return
    setDepartmentLoading(true)
    setDepartmentError('')
    try {
      const targetPage = pageOverride ?? departmentPage
      const targetQuery = (queryOverride ?? departmentSearch).trim()
      const params = new URLSearchParams()
      params.set('org_id', String(auth.user.org_id))
      params.set('page', String(targetPage))
      params.set('page_size', String(departmentPageSize))
      params.set('sort_by', departmentSortBy)
      params.set('sort_dir', departmentSortDir)
      if (targetQuery) params.set('q', targetQuery)
      const data = await apiRequest(`/departments?${params.toString()}`, {
        method: 'GET',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      const results = data?.results ?? data ?? []
      setDepartmentList(results)
      setDepartmentTotal(data?.count ?? results.length ?? 0)
    } catch (err: any) {
      setDepartmentError(err.details?.detail || err.message || 'Failed to load departments.')
    } finally {
      setDepartmentLoading(false)
    }
  }

  const loadAuditLogs = async (pageOverride?: number, queryOverride?: string) => {
    if (!auth?.accessToken || !auth?.user?.org_id) return
    setAuditLoading(true)
    setAuditError('')
    try {
      const targetPage = pageOverride ?? auditPage
      const targetQuery = (queryOverride ?? auditSearch).trim()
      const params = new URLSearchParams()
      params.set('org_id', String(auth.user.org_id))
      params.set('page', String(targetPage))
      params.set('page_size', String(auditPageSize))
      params.set('sort_by', auditSortBy)
      params.set('sort_dir', auditSortDir)
      if (targetQuery) params.set('q', targetQuery)
      const actor = auditActor.trim()
      if (actor) params.set('actor_user_id', actor)
      const action = auditAction.trim()
      if (action) params.set('action', action)
      const targetType = auditTargetType.trim()
      if (targetType) params.set('target_type', targetType)
      if (auditDateFrom) params.set('date_from', auditDateFrom)
      if (auditDateTo) params.set('date_to', auditDateTo)
      const data = await apiRequest(`/audit-logs?${params.toString()}`, {
        method: 'GET',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      const results = data?.results ?? data ?? []
      setAuditLogs(results)
      setAuditTotal(data?.count ?? results.length ?? 0)
    } catch (err: any) {
      setAuditError(err.details?.detail || err.message || 'Failed to load audit logs.')
    } finally {
      setAuditLoading(false)
    }
  }

  const loadUserDepartmentAssignments = async (userId: number) => {
    if (!auth?.accessToken) return
    setDepartmentAssignLoading(true)
    setDepartmentAssignError('')
    try {
      const data = await apiRequest(`/users/${userId}/departments`, {
        method: 'GET',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      setDepartmentAssignments(data || [])
    } catch (err: any) {
      setDepartmentAssignError(err.details?.detail || err.message || 'Failed to load departments.')
    } finally {
      setDepartmentAssignLoading(false)
    }
  }

  const openDepartmentAssignments = async (user: { id: number; display_name: string }) => {
    setDepartmentAssignUserId(user.id)
    setDepartmentAssignUserName(user.display_name)
    setDepartmentAssignments([])
    setDepartmentAssignError('')
    setShowDepartmentAssign(true)
    if (departmentList.length === 0) {
      await loadDepartmentList(1)
    }
    if (propertyList.length === 0) {
      await loadPropertyList()
    }
    await loadUserDepartmentAssignments(user.id)
  }

  const isDepartmentAssigned = (departmentId: number) =>
    departmentAssignments.some((assignment) => assignment.department_id === departmentId)
  const primaryDepartmentId =
    departmentAssignments.find((assignment) => assignment.is_primary)?.department_id ?? null

  const onAssignDepartment = async (departmentId: number, makePrimary = false) => {
    if (!auth?.accessToken || !departmentAssignUserId) return
    setDepartmentAssignLoading(true)
    setDepartmentAssignError('')
    try {
      await apiRequest(`/users/${departmentAssignUserId}/departments`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
        body: JSON.stringify({ department_id: departmentId, is_primary: makePrimary }),
      })
      await loadUserDepartmentAssignments(departmentAssignUserId)
    } catch (err: any) {
      setDepartmentAssignError(err.details?.detail || err.message || 'Failed to assign department.')
    } finally {
      setDepartmentAssignLoading(false)
    }
  }

  const onUnassignDepartment = async (departmentId: number) => {
    if (!auth?.accessToken || !departmentAssignUserId) return
    setDepartmentAssignLoading(true)
    setDepartmentAssignError('')
    try {
      await apiRequest(`/users/${departmentAssignUserId}/departments/${departmentId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      await loadUserDepartmentAssignments(departmentAssignUserId)
    } catch (err: any) {
      setDepartmentAssignError(err.details?.detail || err.message || 'Failed to unassign department.')
    } finally {
      setDepartmentAssignLoading(false)
    }
  }

  const loadUserRoles = async (userId: number) => {
    if (!auth?.accessToken) return
    setUserRoleLoading(true)
    setUserRoleError('')
    try {
      const data = await apiRequest(`/users/${userId}/roles`, {
        method: 'GET',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      setUserRoleAssignments(data || [])
    } catch (err: any) {
      setUserRoleError(err.details?.detail || err.message || 'Failed to load roles.')
    } finally {
      setUserRoleLoading(false)
    }
  }

  const openUserRoles = async (user: { id: number; display_name: string }) => {
    setRoleAssignUserId(user.id)
    setRoleAssignUserName(user.display_name)
    setUserRoleAssignments([])
    setUserRoleError('')
    setShowUserRoles(true)
    if (roles.length === 0) {
      await loadRoleList(1)
    }
    await loadUserRoles(user.id)
  }

  const isRoleAssigned = (roleId: number) =>
    userRoleAssignments.some((assignment) => assignment.role_id === roleId)

  const onAssignRole = async (roleId: number) => {
    if (!auth?.accessToken || !roleAssignUserId) return
    setUserRoleLoading(true)
    setUserRoleError('')
    try {
      await apiRequest(`/users/${roleAssignUserId}/roles`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
        body: JSON.stringify({ role_id: roleId }),
      })
      await loadUserRoles(roleAssignUserId)
    } catch (err: any) {
      setUserRoleError(err.details?.detail || err.message || 'Failed to assign role.')
    } finally {
      setUserRoleLoading(false)
    }
  }

  const onUnassignRole = async (roleId: number) => {
    if (!auth?.accessToken || !roleAssignUserId) return
    setUserRoleLoading(true)
    setUserRoleError('')
    try {
      await apiRequest(`/users/${roleAssignUserId}/roles/${roleId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      await loadUserRoles(roleAssignUserId)
    } catch (err: any) {
      setUserRoleError(err.details?.detail || err.message || 'Failed to remove role.')
    } finally {
      setUserRoleLoading(false)
    }
  }

  const openDepartmentModal = (dept?: any) => {
    if (dept) {
      setDepartmentEditingId(dept.id)
      setDepartmentForm({
        property_id: dept.property_id ? String(dept.property_id) : '',
        name: dept.name,
        description: dept.description || '',
      })
    } else {
      setDepartmentEditingId(null)
      setDepartmentForm({
        property_id: '',
        name: '',
        description: '',
      })
    }
    setDepartmentError('')
    setShowDepartmentModal(true)
  }

  const onDepartmentChange = (key: keyof typeof departmentForm) =>
    (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      setDepartmentForm((prev) => ({ ...prev, [key]: event.target.value }))
    }

  const onSaveDepartment = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!auth?.accessToken || !auth?.user?.org_id) return
    setDepartmentSaving(true)
    setDepartmentError('')
    try {
      const propertyValue = departmentForm.property_id ? Number(departmentForm.property_id) : undefined
      const payload = {
        org_id: auth.user.org_id,
        property_id: propertyValue,
        name: departmentForm.name.trim(),
        description: departmentForm.description.trim(),
      }
      if (departmentEditingId) {
        if (!departmentForm.property_id) {
          payload.property_id = null as any
        }
        await apiRequest(`/departments/${departmentEditingId}`, {
          method: 'PATCH',
          headers: { Authorization: `Bearer ${auth.accessToken}` },
          body: JSON.stringify(payload),
        })
      } else {
        await apiRequest('/departments', {
          method: 'POST',
          headers: { Authorization: `Bearer ${auth.accessToken}` },
          body: JSON.stringify(payload),
        })
      }
      setShowDepartmentModal(false)
      await loadDepartmentList()
    } catch (err: any) {
      setDepartmentError(err.details?.detail || err.message || 'Failed to save department.')
    } finally {
      setDepartmentSaving(false)
    }
  }

  const onDeleteDepartment = async (departmentId: number) => {
    if (!auth?.accessToken) return
    const ok = window.confirm('Delete this department?')
    if (!ok) return
    try {
      await apiRequest(`/departments/${departmentId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      await loadDepartmentList()
    } catch (err: any) {
      setDepartmentError(err.details?.detail || err.message || 'Failed to delete department.')
    }
  }

  const openPropertyModal = (prop?: any) => {
    if (prop) {
      setPropertyEditingId(prop.id)
      setPropertyForm({
        code: prop.code,
        name: prop.name,
        timezone: prop.timezone,
        address_line1: prop.address_line1 || '',
        address_line2: prop.address_line2 || '',
        city: prop.city,
        state: prop.state || '',
        postal_code: prop.postal_code || '',
        country: prop.country,
      })
    } else {
      setPropertyEditingId(null)
      setPropertyForm({
        code: '',
        name: '',
        timezone: '',
        address_line1: '',
        address_line2: '',
        city: '',
        state: '',
        postal_code: '',
        country: '',
      })
    }
    setPropertyError('')
    setShowPropertyModal(true)
  }

  const onPropertyChange = (key: keyof typeof propertyForm) => (event: ChangeEvent<HTMLInputElement>) => {
    setPropertyForm((prev) => ({ ...prev, [key]: event.target.value }))
  }

  const onPropertySelectChange = (key: keyof typeof propertyForm) => (event: ChangeEvent<HTMLSelectElement>) => {
    setPropertyForm((prev) => ({ ...prev, [key]: event.target.value }))
  }

  const onSaveProperty = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!auth?.accessToken || !auth?.user?.org_id) return
    setPropertySaving(true)
    setPropertyError('')
    try {
      if (propertyEditingId) {
        await apiRequest(`/properties/${propertyEditingId}`, {
          method: 'PATCH',
          headers: { Authorization: `Bearer ${auth.accessToken}` },
          body: JSON.stringify({
            code: propertyForm.code.trim(),
            name: propertyForm.name.trim(),
            timezone: propertyForm.timezone.trim(),
            address_line1: propertyForm.address_line1.trim(),
            address_line2: propertyForm.address_line2.trim(),
            city: propertyForm.city.trim(),
            state: propertyForm.state.trim(),
            postal_code: propertyForm.postal_code.trim(),
            country: propertyForm.country.trim(),
          }),
        })
      } else {
        await apiRequest('/properties', {
          method: 'POST',
          headers: { Authorization: `Bearer ${auth.accessToken}` },
          body: JSON.stringify({
            org_id: auth.user.org_id,
            code: propertyForm.code.trim(),
            name: propertyForm.name.trim(),
            timezone: propertyForm.timezone.trim(),
            address_line1: propertyForm.address_line1.trim(),
            address_line2: propertyForm.address_line2.trim(),
            city: propertyForm.city.trim(),
            state: propertyForm.state.trim(),
            postal_code: propertyForm.postal_code.trim(),
            country: propertyForm.country.trim(),
          }),
        })
      }
      setShowPropertyModal(false)
      await loadPropertyList()
    } catch (err: any) {
      setPropertyError(err.details?.detail || err.message || 'Failed to save property.')
    } finally {
      setPropertySaving(false)
    }
  }

  const onDeleteProperty = async (propertyId: number) => {
    if (!auth?.accessToken) return
    const ok = window.confirm('Delete this property?')
    if (!ok) return
    try {
      await apiRequest(`/properties/${propertyId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      await loadPropertyList()
    } catch (err: any) {
      setPropertyError(err.details?.detail || err.message || 'Failed to delete property.')
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
  const formatDateTime = (value?: string) => {
    if (!value) return '-'
    const date = new Date(value)
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
  }

  return (
    <div className="page full">
      {(inviteMessage || editMessage) && <div className="toast">{inviteMessage || editMessage}</div>}
      <div className="dashboard">
        <aside className="sidebar-lite">
          <div className="brand">
            <div className="avatar">{initials}</div>
            <div>
              <div className="brand-title">Service Ticketing</div>
              <div className="brand-sub">{orgName || 'Organization'}</div>
              <div className="brand-sub secondary">{displayName}</div>
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
            {canViewUsers && (
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
            )}
            {canViewRoles && (
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
            )}
            {canViewPermissions && (
              <button
                className={`menu-item ${activeMenu === 'permissions' ? 'active' : ''}`}
                onClick={() => setActiveMenu('permissions')}
              >
                <span className="icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
                    <path d="M4 11h16" />
                    <path d="M7 7h10" />
                    <path d="M9 15h6" />
                  </svg>
                </span>
                <span>Permission Management</span>
              </button>
            )}
            {canViewOrgs && (
              <button
                className={`menu-item ${activeMenu === 'orgs' ? 'active' : ''}`}
                onClick={() => setActiveMenu('orgs')}
              >
                <span className="icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
                    <path d="M4 4h16v16H4z" />
                    <path d="M8 8h8M8 12h8M8 16h8" />
                  </svg>
                </span>
                <span>Organization Management</span>
              </button>
            )}
            {canViewProperties && (
              <button
                className={`menu-item ${activeMenu === 'properties' ? 'active' : ''}`}
                onClick={() => setActiveMenu('properties')}
              >
                <span className="icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
                    <path d="M4 7h16v13H4z" />
                    <path d="M8 7V4h8v3" />
                  </svg>
                </span>
                <span>Property Management</span>
              </button>
            )}
            {canViewDepartments && (
              <button
                className={`menu-item ${activeMenu === 'departments' ? 'active' : ''}`}
                onClick={() => setActiveMenu('departments')}
              >
                <span className="icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
                    <path d="M4 4h16v16H4z" />
                    <path d="M8 8h8M8 12h8M8 16h6" />
                  </svg>
                </span>
                <span>Department Management</span>
              </button>
            )}
            {canViewAudit && (
              <button
                className={`menu-item ${activeMenu === 'audit' ? 'active' : ''}`}
                onClick={() => setActiveMenu('audit')}
              >
                <span className="icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
                    <path d="M4 4h16v16H4z" />
                    <path d="M8 8h8M8 12h8M8 16h8" />
                  </svg>
                </span>
                <span>Audit Logs</span>
              </button>
            )}
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
                  {canManageUsers && (
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
                  <div className="list-header user-header">
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
                    <div key={user.id} className="list-item user-row">
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
                        {canManageUsers && (
                          <button className="button secondary small" onClick={() => openEdit(user)}>
                            Edit
                          </button>
                        )}
                        {canManageUsers && (
                          <button
                            className="button secondary small"
                            onClick={() => openUserRoles({ id: user.id, display_name: user.display_name })}
                          >
                            Roles
                          </button>
                        )}
                        {canManageUsers && (
                          <button
                            className="button secondary small"
                            onClick={() => openPropertyAssignments({ id: user.id, display_name: user.display_name })}
                          >
                            Properties
                          </button>
                        )}
                        {canManageUsers && (
                          <button
                            className="button secondary small"
                            onClick={() => openDepartmentAssignments({ id: user.id, display_name: user.display_name })}
                          >
                            Departments
                          </button>
                        )}
                        {canManageUsers && user.status === 'invited' && (
                          <button
                            className="button secondary small"
                            onClick={() => resendInvite(user.id)}
                            disabled={inviteLoadingId === user.id}
                          >
                            {inviteLoadingId === user.id ? 'Resending...' : 'Resend Invite'}
                          </button>
                        )}
                        {canManageUsers && user.status === 'active' && (
                          <button
                            className="button secondary small"
                            onClick={async () => {
                              if (!auth?.accessToken) return
                              await apiRequest(`/users/${user.id}/suspend`, {
                                method: 'POST',
                                headers: { Authorization: `Bearer ${auth.accessToken}` },
                              })
                              await loadUsers(page)
                            }}
                          >
                            Suspend
                          </button>
                        )}
                        {canManageUsers && user.status === 'suspended' && (
                          <button
                            className="button secondary small"
                            onClick={async () => {
                              if (!auth?.accessToken) return
                              await apiRequest(`/users/${user.id}/reactivate`, {
                                method: 'POST',
                                headers: { Authorization: `Bearer ${auth.accessToken}` },
                              })
                              await loadUsers(page)
                            }}
                          >
                            Reactivate
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
                  {canManageRoles && (
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
                  <div className="list-header role-header">
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
                        {canManageRoles && (
                          <button className="button secondary small" onClick={() => openRoleModal(role)}>
                            Edit
                          </button>
                        )}
                        {canManageRoles && (
                          <button className="button secondary small" onClick={() => openRolePermissions(role)}>
                            Permissions
                          </button>
                        )}
                        {canManageRoles && (
                          <button className="button secondary small" onClick={() => onDeleteRole(role.id)}>
                            Delete
                          </button>
                        )}
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
          {activeMenu === 'permissions' && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
                <div>
                  <h2>Permission Management</h2>
                  <p className="helper">Define and manage permissions.</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <input
                    className="input"
                    placeholder="Search permissions"
                    value={permissionSearch}
                    onChange={(event) => {
                      setPermissionPage(1)
                      setPermissionSearch(event.target.value)
                    }}
                    style={{ minWidth: '220px' }}
                  />
                  <button className="button secondary small" onClick={() => loadPermissionList(1)}>
                    Search
                  </button>
                  {canManagePermissions && (
                    <button className="button primary small icon-button" onClick={() => openPermissionModal()}>
                      <span className="icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                          <path d="M12 5v14M5 12h14" />
                        </svg>
                      </span>
                      Add Permission
                    </button>
                  )}
                </div>
              </div>
              {permissionLoading && <p className="helper">Loading permissions...</p>}
              {permissionError && <p className="error">{permissionError}</p>}
              {!permissionLoading && !permissionError && (
                <div className="list">
                  <div className="list-header permission-header">
                    <button
                      className="header-button"
                      onClick={() => {
                        if (permissionSortBy === 'code') {
                          setPermissionSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
                        } else {
                          setPermissionSortBy('code')
                          setPermissionSortDir('asc')
                        }
                      }}
                    >
                      Code
                      {permissionSortBy === 'code' && (
                        <span className="sort-indicator">{permissionSortDir === 'asc' ? '▲' : '▼'}</span>
                      )}
                    </button>
                    <span>Description</span>
                    <span>Actions</span>
                  </div>
                  {permissionList.map((perm) => (
                    <div key={perm.id} className="list-item permission-row">
                      <div className="cell">{perm.code}</div>
                      <div className="cell">{perm.description || '-'}</div>
                      <div className="cell actions">
                        {canManagePermissions && (
                          <button className="button secondary small" onClick={() => openPermissionModal(perm)}>
                            Edit
                          </button>
                        )}
                        {canManagePermissions && (
                          <button className="button secondary small" onClick={() => onDeletePermission(perm.id)}>
                            Delete
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {!permissionLoading && !permissionError && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
                  <span className="helper">
                    Showing {permissionList.length === 0 ? 0 : (permissionPage - 1) * permissionPageSize + 1}-
                    {(permissionPage - 1) * permissionPageSize + permissionList.length} of {permissionTotal}
                  </span>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      className="button secondary small"
                      onClick={() => setPermissionPage((prev) => Math.max(prev - 1, 1))}
                      disabled={permissionPage <= 1}
                    >
                      Prev
                    </button>
                    <button
                      className="button secondary small"
                      onClick={() => setPermissionPage((prev) => prev + 1)}
                      disabled={permissionPage * permissionPageSize >= permissionTotal}
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
          {activeMenu === 'orgs' && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
                <div>
                  <h2>Organization Management</h2>
                  <p className="helper">Manage organizations.</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <input
                    className="input"
                    placeholder="Search organizations"
                    value={orgSearch}
                    onChange={(event) => {
                      setOrgPage(1)
                      setOrgSearch(event.target.value)
                    }}
                    style={{ minWidth: '220px' }}
                  />
                  <button className="button secondary small" onClick={() => loadOrgList()}>
                    Search
                  </button>
                  {canManageOrgs && (
                    <button className="button primary small icon-button" onClick={() => openOrgModal()}>
                      <span className="icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                          <path d="M12 5v14M5 12h14" />
                        </svg>
                      </span>
                      Add Organization
                    </button>
                  )}
                </div>
              </div>
              {orgLoading && <p className="helper">Loading organizations...</p>}
              {orgError && <p className="error">{orgError}</p>}
              {!orgLoading && !orgError && (
                <div className="list">
                  <div className="list-header org-header">
                    <button
                      className="header-button"
                      onClick={() => {
                        if (orgSortBy === 'id') {
                          setOrgSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
                        } else {
                          setOrgSortBy('id')
                          setOrgSortDir('asc')
                        }
                      }}
                    >
                      ID
                      {orgSortBy === 'id' && <span className="sort-indicator">{orgSortDir === 'asc' ? '▲' : '▼'}</span>}
                    </button>
                    <button
                      className="header-button"
                      onClick={() => {
                        if (orgSortBy === 'name') {
                          setOrgSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
                        } else {
                          setOrgSortBy('name')
                          setOrgSortDir('asc')
                        }
                      }}
                    >
                      Name
                      {orgSortBy === 'name' && <span className="sort-indicator">{orgSortDir === 'asc' ? '▲' : '▼'}</span>}
                    </button>
                    <button
                      className="header-button"
                      onClick={() => {
                        if (orgSortBy === 'legal_name') {
                          setOrgSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
                        } else {
                          setOrgSortBy('legal_name')
                          setOrgSortDir('asc')
                        }
                      }}
                    >
                      Legal Name
                      {orgSortBy === 'legal_name' && <span className="sort-indicator">{orgSortDir === 'asc' ? '▲' : '▼'}</span>}
                    </button>
                    <button
                      className="header-button"
                      onClick={() => {
                        if (orgSortBy === 'status') {
                          setOrgSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
                        } else {
                          setOrgSortBy('status')
                          setOrgSortDir('asc')
                        }
                      }}
                    >
                      Status
                      {orgSortBy === 'status' && <span className="sort-indicator">{orgSortDir === 'asc' ? '▲' : '▼'}</span>}
                    </button>
                    <span>Actions</span>
                  </div>
                  {orgList.map((org) => (
                    <div key={org.id} className="list-item org-row">
                      <div className="cell">{org.id}</div>
                      <div className="cell">{org.name}</div>
                      <div className="cell">{org.legal_name}</div>
                      <div className="cell">
                        <span className={`status ${org.status}`}>{org.status}</span>
                      </div>
                      <div className="cell actions">
                        {canManageOrgs && (
                          <button className="button secondary small" onClick={() => openOrgModal(org)}>
                            Edit
                          </button>
                        )}
                        {canManageOrgs && (
                          <button className="button secondary small" onClick={() => onDeleteOrg(org.id)}>
                            Delete
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {!orgLoading && !orgError && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
                  <span className="helper">
                    Showing {orgList.length === 0 ? 0 : (orgPage - 1) * orgPageSize + 1}-
                    {(orgPage - 1) * orgPageSize + orgList.length} of {orgTotal}
                  </span>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      className="button secondary small"
                      onClick={() => setOrgPage((prev) => Math.max(prev - 1, 1))}
                      disabled={orgPage <= 1}
                    >
                      Prev
                    </button>
                    <button
                      className="button secondary small"
                      onClick={() => setOrgPage((prev) => prev + 1)}
                      disabled={orgPage * orgPageSize >= orgTotal}
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
          {activeMenu === 'properties' && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
                <div>
                  <h2>Property Management</h2>
                  <p className="helper">Manage properties for this organization.</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <input
                    className="input"
                    placeholder="Search properties"
                    value={propertySearch}
                    onChange={(event) => {
                      setPropertyPage(1)
                      setPropertySearch(event.target.value)
                    }}
                    style={{ minWidth: '220px' }}
                  />
                  <button className="button secondary small" onClick={() => loadPropertyList(1)}>
                    Search
                  </button>
                  {canManageProperties && (
                    <button className="button primary small icon-button" onClick={() => openPropertyModal()}>
                      <span className="icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                          <path d="M12 5v14M5 12h14" />
                        </svg>
                      </span>
                      Add Property
                    </button>
                  )}
                </div>
              </div>
              {propertyLoading && <p className="helper">Loading properties...</p>}
              {propertyError && <p className="error">{propertyError}</p>}
              {!propertyLoading && !propertyError && (
                <div className="list">
                  <div className="list-header property-header">
                    <button
                      className="header-button"
                      onClick={() => {
                        if (propertySortBy === 'code') {
                          setPropertySortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
                        } else {
                          setPropertySortBy('code')
                          setPropertySortDir('asc')
                        }
                      }}
                    >
                      Code
                      {propertySortBy === 'code' && (
                        <span className="sort-indicator">{propertySortDir === 'asc' ? '▲' : '▼'}</span>
                      )}
                    </button>
                    <button
                      className="header-button"
                      onClick={() => {
                        if (propertySortBy === 'name') {
                          setPropertySortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
                        } else {
                          setPropertySortBy('name')
                          setPropertySortDir('asc')
                        }
                      }}
                    >
                      Name
                      {propertySortBy === 'name' && (
                        <span className="sort-indicator">{propertySortDir === 'asc' ? '▲' : '▼'}</span>
                      )}
                    </button>
                    <button
                      className="header-button"
                      onClick={() => {
                        if (propertySortBy === 'city') {
                          setPropertySortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
                        } else {
                          setPropertySortBy('city')
                          setPropertySortDir('asc')
                        }
                      }}
                    >
                      City
                      {propertySortBy === 'city' && (
                        <span className="sort-indicator">{propertySortDir === 'asc' ? '▲' : '▼'}</span>
                      )}
                    </button>
                    <button
                      className="header-button"
                      onClick={() => {
                        if (propertySortBy === 'country') {
                          setPropertySortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
                        } else {
                          setPropertySortBy('country')
                          setPropertySortDir('asc')
                        }
                      }}
                    >
                      Country
                      {propertySortBy === 'country' && (
                        <span className="sort-indicator">{propertySortDir === 'asc' ? '▲' : '▼'}</span>
                      )}
                    </button>
                    <span>Actions</span>
                  </div>
                  {propertyList.map((prop) => (
                    <div key={prop.id} className="list-item property-row">
                      <div className="cell">{prop.code}</div>
                      <div className="cell">{prop.name}</div>
                      <div className="cell">{prop.city}</div>
                      <div className="cell">{prop.country}</div>
                      <div className="cell actions">
                        {canManageProperties && (
                          <button className="button secondary small" onClick={() => openPropertyModal(prop)}>
                            Edit
                          </button>
                        )}
                        {canManageProperties && (
                          <button className="button secondary small" onClick={() => onDeleteProperty(prop.id)}>
                            Delete
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {!propertyLoading && !propertyError && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
                  <span className="helper">
                    Showing {propertyList.length === 0 ? 0 : (propertyPage - 1) * propertyPageSize + 1}-
                    {(propertyPage - 1) * propertyPageSize + propertyList.length} of {propertyTotal}
                  </span>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      className="button secondary small"
                      onClick={() => setPropertyPage((prev) => Math.max(prev - 1, 1))}
                      disabled={propertyPage <= 1}
                    >
                      Prev
                    </button>
                    <button
                      className="button secondary small"
                      onClick={() => setPropertyPage((prev) => prev + 1)}
                      disabled={propertyPage * propertyPageSize >= propertyTotal}
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
          {activeMenu === 'departments' && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
                <div>
                  <h2>Department Management</h2>
                  <p className="helper">Manage departments for this organization.</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <input
                    className="input"
                    placeholder="Search departments"
                    value={departmentSearch}
                    onChange={(event) => {
                      setDepartmentPage(1)
                      setDepartmentSearch(event.target.value)
                    }}
                    style={{ minWidth: '220px' }}
                  />
                  <button className="button secondary small" onClick={() => loadDepartmentList(1)}>
                    Search
                  </button>
                  {canManageDepartments && (
                    <button className="button primary small icon-button" onClick={() => openDepartmentModal()}>
                      <span className="icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                          <path d="M12 5v14M5 12h14" />
                        </svg>
                      </span>
                      Add Department
                    </button>
                  )}
                </div>
              </div>
              {departmentLoading && <p className="helper">Loading departments...</p>}
              {departmentError && <p className="error">{departmentError}</p>}
              {!departmentLoading && !departmentError && (
                <div className="list">
                  <div className="list-header department-header">
                    <button
                      className="header-button"
                      onClick={() => {
                        if (departmentSortBy === 'name') {
                          setDepartmentSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
                        } else {
                          setDepartmentSortBy('name')
                          setDepartmentSortDir('asc')
                        }
                      }}
                    >
                      Name
                      {departmentSortBy === 'name' && (
                        <span className="sort-indicator">{departmentSortDir === 'asc' ? '▲' : '▼'}</span>
                      )}
                    </button>
                    <span>Property</span>
                    <span>Description</span>
                    <button
                      className="header-button"
                      onClick={() => {
                        if (departmentSortBy === 'created_at') {
                          setDepartmentSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
                        } else {
                          setDepartmentSortBy('created_at')
                          setDepartmentSortDir('asc')
                        }
                      }}
                    >
                      Created
                      {departmentSortBy === 'created_at' && (
                        <span className="sort-indicator">{departmentSortDir === 'asc' ? '▲' : '▼'}</span>
                      )}
                    </button>
                    <span>Actions</span>
                  </div>
                  {departmentList.map((dept) => {
                    const propertyName =
                      dept.property_id
                        ? propertyList.find((prop) => prop.id === dept.property_id)?.name || `#${dept.property_id}`
                        : 'All Properties'
                    return (
                      <div key={dept.id} className="list-item department-row">
                        <div className="cell">{dept.name}</div>
                        <div className="cell">{propertyName}</div>
                        <div className="cell">{dept.description || '-'}</div>
                        <div className="cell">{dept.created_at ? new Date(dept.created_at).toLocaleDateString() : '-'}</div>
                        <div className="cell actions">
                          {canManageDepartments && (
                            <button className="button secondary small" onClick={() => openDepartmentModal(dept)}>
                              Edit
                            </button>
                          )}
                          {canManageDepartments && (
                            <button className="button secondary small" onClick={() => onDeleteDepartment(dept.id)}>
                              Delete
                            </button>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
              {!departmentLoading && !departmentError && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
                  <span className="helper">
                    Showing {departmentList.length === 0 ? 0 : (departmentPage - 1) * departmentPageSize + 1}-
                    {(departmentPage - 1) * departmentPageSize + departmentList.length} of {departmentTotal}
                  </span>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      className="button secondary small"
                      onClick={() => setDepartmentPage((prev) => Math.max(prev - 1, 1))}
                      disabled={departmentPage <= 1}
                    >
                      Prev
                    </button>
                    <button
                      className="button secondary small"
                      onClick={() => setDepartmentPage((prev) => prev + 1)}
                      disabled={departmentPage * departmentPageSize >= departmentTotal}
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
          {activeMenu === 'audit' && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
                <div>
                  <h2>Audit Logs</h2>
                  <p className="helper">Search and review recent activity across your organization.</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <input
                    className="input"
                    placeholder="Search logs"
                    value={auditSearch}
                    onChange={(event) => {
                      setAuditPage(1)
                      setAuditSearch(event.target.value)
                    }}
                    style={{ minWidth: '220px' }}
                  />
                  <button className="button secondary small" onClick={() => loadAuditLogs(1)}>
                    Search
                  </button>
                </div>
              </div>
              <div className="audit-filters">
                <input
                  className="input"
                  placeholder="Actor ID"
                  value={auditActor}
                  onChange={(event) => {
                    setAuditPage(1)
                    setAuditActor(event.target.value)
                  }}
                />
                <input
                  className="input"
                  placeholder="Action"
                  value={auditAction}
                  onChange={(event) => {
                    setAuditPage(1)
                    setAuditAction(event.target.value)
                  }}
                />
                <input
                  className="input"
                  placeholder="Target type"
                  value={auditTargetType}
                  onChange={(event) => {
                    setAuditPage(1)
                    setAuditTargetType(event.target.value)
                  }}
                />
                <input
                  className="input"
                  type="date"
                  value={auditDateFrom}
                  onChange={(event) => {
                    setAuditPage(1)
                    setAuditDateFrom(event.target.value)
                  }}
                />
                <input
                  className="input"
                  type="date"
                  value={auditDateTo}
                  onChange={(event) => {
                    setAuditPage(1)
                    setAuditDateTo(event.target.value)
                  }}
                />
                <button
                  className="button secondary small"
                  onClick={() => {
                    setAuditActor('')
                    setAuditAction('')
                    setAuditTargetType('')
                    setAuditDateFrom('')
                    setAuditDateTo('')
                    setAuditPage(1)
                  }}
                >
                  Clear
                </button>
              </div>
              {auditLoading && <p className="helper">Loading audit logs...</p>}
              {auditError && <p className="error">{auditError}</p>}
              {!auditLoading && !auditError && (
                <div className="list">
                  <div className="list-header audit-header">
                    <button
                      className="header-button"
                      onClick={() => {
                        if (auditSortBy === 'created_at') {
                          setAuditSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
                        } else {
                          setAuditSortBy('created_at')
                          setAuditSortDir('desc')
                        }
                      }}
                    >
                      Time
                      {auditSortBy === 'created_at' && (
                        <span className="sort-indicator">{auditSortDir === 'asc' ? '▲' : '▼'}</span>
                      )}
                    </button>
                    <button
                      className="header-button"
                      onClick={() => {
                        if (auditSortBy === 'action') {
                          setAuditSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
                        } else {
                          setAuditSortBy('action')
                          setAuditSortDir('asc')
                        }
                      }}
                    >
                      Action
                      {auditSortBy === 'action' && (
                        <span className="sort-indicator">{auditSortDir === 'asc' ? '▲' : '▼'}</span>
                      )}
                    </button>
                    <button
                      className="header-button"
                      onClick={() => {
                        if (auditSortBy === 'target_type') {
                          setAuditSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))
                        } else {
                          setAuditSortBy('target_type')
                          setAuditSortDir('asc')
                        }
                      }}
                    >
                      Target
                      {auditSortBy === 'target_type' && (
                        <span className="sort-indicator">{auditSortDir === 'asc' ? '▲' : '▼'}</span>
                      )}
                    </button>
                    <span>Actor</span>
                    <span>IP</span>
                  </div>
                  {auditLogs.map((log) => (
                    <div key={log.id} className="list-item audit-row">
                      <div className="cell">{formatDateTime(log.created_at)}</div>
                      <div className="cell">{log.action}</div>
                      <div className="cell">
                        {log.target_type} #{log.target_id}
                      </div>
                      <div className="cell">{log.actor_user_id ?? '-'}</div>
                      <div className="cell">{log.ip_address || '-'}</div>
                    </div>
                  ))}
                </div>
              )}
              {!auditLoading && !auditError && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
                  <span className="helper">
                    Showing {auditLogs.length === 0 ? 0 : (auditPage - 1) * auditPageSize + 1}-
                    {(auditPage - 1) * auditPageSize + auditLogs.length} of {auditTotal}
                  </span>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      className="button secondary small"
                      onClick={() => setAuditPage((prev) => Math.max(prev - 1, 1))}
                      disabled={auditPage <= 1}
                    >
                      Prev
                    </button>
                    <button
                      className="button secondary small"
                      onClick={() => setAuditPage((prev) => prev + 1)}
                      disabled={auditPage * auditPageSize >= auditTotal}
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
                    Roles
                    <div className="checkbox-list">
                      {roles.map((role) => (
                        <label key={role.id} className="checkbox-row">
                          <input
                            type="checkbox"
                            checked={editRoleIds.includes(role.id)}
                            onChange={(event) => onEditRoleToggle(role.id, event.target.checked)}
                          />
                          <span>{role.name}</span>
                        </label>
                      ))}
                    </div>
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
          {showPropertyAssign && (
            <div className="modal-backdrop" onClick={() => setShowPropertyAssign(false)}>
              <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
                <h3>Property Assignments — {assignUserName}</h3>
                <p className="helper">Assign this user to one or more properties. Primary is the default property when the user logs in.</p>
                {assignmentError && <p className="error">{assignmentError}</p>}
                {assignmentLoading && <p className="helper">Loading assignments...</p>}
                {!assignmentLoading && (
                  <div className="assignment-list">
                    <div className="assignment-header department-assign-header">
                      <span>Property</span>
                      <span>Code</span>
                      <span>Primary</span>
                      <span>Actions</span>
                    </div>
                    {propertyList.length === 0 && (
                      <div className="assignment-row empty">No properties available.</div>
                    )}
                    {propertyList.map((prop) => {
                      const assigned = isAssigned(prop.id)
                      const isPrimary = primaryPropertyId === prop.id
                      return (
                        <div key={prop.id} className="assignment-row">
                          <span className="name">{prop.name}</span>
                          <span className="code">{prop.code}</span>
                          <span className="primary">{isPrimary ? 'Primary' : '-'}</span>
                          <span className="actions">
                            {assigned ? (
                              <>
                                {!isPrimary && (
                                  <button
                                    className="button secondary small"
                                    onClick={() => onAssignProperty(prop.id, true)}
                                    disabled={assignmentLoading}
                                  >
                                    Set Primary
                                  </button>
                                )}
                                <button
                                  className="button secondary small"
                                  onClick={() => onUnassignProperty(prop.id)}
                                  disabled={assignmentLoading}
                                >
                                  Unassign
                                </button>
                              </>
                            ) : (
                              <button
                                className="button secondary small"
                                onClick={() => onAssignProperty(prop.id, false)}
                                disabled={assignmentLoading}
                              >
                                Assign
                              </button>
                            )}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                )}
                <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '16px' }}>
                  <button type="button" className="button secondary small" onClick={() => setShowPropertyAssign(false)}>
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}
          {showDepartmentAssign && (
            <div className="modal-backdrop" onClick={() => setShowDepartmentAssign(false)}>
              <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
                <h3>Department Assignments — {departmentAssignUserName}</h3>
                <p className="helper">Assign this user to one or more departments. Primary is the default department.</p>
                {departmentAssignError && <p className="error">{departmentAssignError}</p>}
                {departmentAssignLoading && <p className="helper">Loading assignments...</p>}
                {!departmentAssignLoading && (
                  <div className="assignment-list">
                    <div className="assignment-header department-assign-header">
                      <span>Department</span>
                      <span>Property</span>
                      <span>Primary</span>
                      <span>Actions</span>
                    </div>
                    {departmentList.length === 0 && (
                      <div className="assignment-row empty">No departments available.</div>
                    )}
                    {departmentList.map((dept) => {
                      const assigned = isDepartmentAssigned(dept.id)
                      const isPrimary = primaryDepartmentId === dept.id
                      const propertyName =
                        dept.property_id
                          ? propertyList.find((prop) => prop.id === dept.property_id)?.name || `#${dept.property_id}`
                          : 'All Properties'
                      return (
                        <div key={dept.id} className="assignment-row department-assign-row">
                          <span className="name">{dept.name}</span>
                          <span className="code">{propertyName}</span>
                          <span className="primary">{isPrimary ? 'Primary' : '-'}</span>
                          <span className="actions">
                            {assigned ? (
                              <>
                                {!isPrimary && (
                                  <button
                                    className="button secondary small"
                                    onClick={() => onAssignDepartment(dept.id, true)}
                                    disabled={departmentAssignLoading}
                                  >
                                    Set Primary
                                  </button>
                                )}
                                <button
                                  className="button secondary small"
                                  onClick={() => onUnassignDepartment(dept.id)}
                                  disabled={departmentAssignLoading}
                                >
                                  Unassign
                                </button>
                              </>
                            ) : (
                              <button
                                className="button secondary small"
                                onClick={() => onAssignDepartment(dept.id, false)}
                                disabled={departmentAssignLoading}
                              >
                                Assign
                              </button>
                            )}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                )}
                <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '16px' }}>
                  <button type="button" className="button secondary small" onClick={() => setShowDepartmentAssign(false)}>
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}
          {showUserRoles && (
            <div className="modal-backdrop" onClick={() => setShowUserRoles(false)}>
              <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
                <h3>User Roles — {roleAssignUserName}</h3>
                <p className="helper">Assign one or more roles to this user.</p>
                {userRoleError && <p className="error">{userRoleError}</p>}
                {userRoleLoading && <p className="helper">Loading roles...</p>}
                {!userRoleLoading && (
                  <div className="assignment-list">
                    <div className="assignment-header permission-assign-header">
                      <span>Role</span>
                      <span>Description</span>
                      <span>Actions</span>
                    </div>
                    {roleList.length === 0 && (
                      <div className="assignment-row empty">No roles available.</div>
                    )}
                    {roleList.map((role) => {
                      const assigned = isRoleAssigned(role.id)
                      return (
                        <div key={role.id} className="assignment-row permission-assign-row">
                          <span className="name">{role.name}</span>
                          <span className="code">{role.description || '-'}</span>
                          <span className="actions">
                            {assigned ? (
                              <button
                                className="button secondary small"
                                onClick={() => onUnassignRole(role.id)}
                                disabled={userRoleLoading}
                              >
                                Remove
                              </button>
                            ) : (
                              <button
                                className="button secondary small"
                                onClick={() => onAssignRole(role.id)}
                                disabled={userRoleLoading}
                              >
                                Assign
                              </button>
                            )}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                )}
                <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '16px' }}>
                  <button type="button" className="button secondary small" onClick={() => setShowUserRoles(false)}>
                    Close
                  </button>
                </div>
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
          {showPermissionModal && (
            <div className="modal-backdrop" onClick={() => setShowPermissionModal(false)}>
              <div className="modal" onClick={(e) => e.stopPropagation()}>
                <h3>{permissionEditingId ? 'Edit Permission' : 'Add Permission'}</h3>
                <form onSubmit={onSavePermission} style={{ display: 'grid', gap: '12px' }}>
                  <label>
                    Code
                    <input
                      className="input"
                      value={permissionForm.code}
                      onChange={onPermissionChange('code')}
                      required
                    />
                  </label>
                  <label>
                    Description
                    <textarea
                      className="input"
                      rows={3}
                      value={permissionForm.description}
                      onChange={onPermissionChange('description')}
                    />
                  </label>
                  {permissionError && <p className="error">{permissionError}</p>}
                  <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                    <button type="button" className="button secondary small" onClick={() => setShowPermissionModal(false)}>
                      Cancel
                    </button>
                    <button className="button small" disabled={permissionSaving}>
                      {permissionSaving ? 'Saving...' : 'Save'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
          {showRolePermissions && (
            <div className="modal-backdrop" onClick={() => setShowRolePermissions(false)}>
              <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
                <h3>Role Permissions — {activeRoleName}</h3>
                <p className="helper">Assign permissions to this role.</p>
                {rolePermissionError && <p className="error">{rolePermissionError}</p>}
                {rolePermissionLoading && <p className="helper">Loading permissions...</p>}
                {!rolePermissionLoading && (
                  <div className="assignment-list">
                    <div className="assignment-header permission-assign-header">
                      <span>Code</span>
                      <span>Description</span>
                      <span>Actions</span>
                    </div>
                    {permissionList.length === 0 && (
                      <div className="assignment-row empty">No permissions available.</div>
                    )}
                    {permissionList.map((perm) => {
                      const assigned = isPermissionAssigned(perm.id)
                      return (
                        <div key={perm.id} className="assignment-row permission-assign-row">
                          <span className="name">{perm.code}</span>
                          <span className="code">{perm.description || '-'}</span>
                          <span className="actions">
                            {assigned ? (
                              <button
                                className="button secondary small"
                                onClick={() => onUnassignPermission(perm.id)}
                                disabled={rolePermissionLoading}
                              >
                                Unassign
                              </button>
                            ) : (
                              <button
                                className="button secondary small"
                                onClick={() => onAssignPermission(perm.id)}
                                disabled={rolePermissionLoading}
                              >
                                Assign
                              </button>
                            )}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                )}
                <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '16px' }}>
                  <button type="button" className="button secondary small" onClick={() => setShowRolePermissions(false)}>
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}
          {showOrgModal && (
            <div className="modal-backdrop" onClick={() => setShowOrgModal(false)}>
              <div className="modal" onClick={(e) => e.stopPropagation()}>
                <h3>{orgEditingId ? 'Edit Organization' : 'Add Organization'}</h3>
                <form onSubmit={onSaveOrg} style={{ display: 'grid', gap: '12px' }}>
                  <label>
                    Name
                    <input
                      className="input"
                      value={orgForm.name}
                      onChange={onOrgChange('name')}
                      required
                    />
                  </label>
                  <label>
                    Legal Name
                    <input
                      className="input"
                      value={orgForm.legal_name}
                      onChange={onOrgChange('legal_name')}
                      required
                    />
                  </label>
                  <label>
                    Status
                    <select className="input" value={orgForm.status} onChange={onOrgChange('status')}>
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                    </select>
                  </label>
                  {orgError && <p className="error">{orgError}</p>}
                  <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                    <button type="button" className="button secondary small" onClick={() => setShowOrgModal(false)}>
                      Cancel
                    </button>
                    <button className="button small" disabled={orgSaving}>
                      {orgSaving ? 'Saving...' : 'Save'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
          {showPropertyModal && (
            <div className="modal-backdrop" onClick={() => setShowPropertyModal(false)}>
              <div className="modal" onClick={(e) => e.stopPropagation()}>
                <h3>{propertyEditingId ? 'Edit Property' : 'Add Property'}</h3>
                <form onSubmit={onSaveProperty} style={{ display: 'grid', gap: '12px' }}>
                  <label>
                    Code
                    <input className="input" value={propertyForm.code} onChange={onPropertyChange('code')} required />
                  </label>
                  <label>
                    Name
                    <input className="input" value={propertyForm.name} onChange={onPropertyChange('name')} required />
                  </label>
                  <label>
                    Timezone
                    <select className="input" value={propertyForm.timezone} onChange={onPropertySelectChange('timezone')} required>
                      <option value="">Select timezone</option>
                      {TIMEZONE_OPTIONS.map((tz) => (
                        <option key={tz} value={tz}>{tz}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Address Line 1
                    <input className="input" value={propertyForm.address_line1} onChange={onPropertyChange('address_line1')} required />
                  </label>
                  <label>
                    Address Line 2
                    <input className="input" value={propertyForm.address_line2} onChange={onPropertyChange('address_line2')} />
                  </label>
                  <label>
                    City
                    <input className="input" value={propertyForm.city} onChange={onPropertyChange('city')} required />
                  </label>
                  <label>
                    State
                    <input className="input" value={propertyForm.state} onChange={onPropertyChange('state')} />
                  </label>
                  <label>
                    Postal Code
                    <input className="input" value={propertyForm.postal_code} onChange={onPropertyChange('postal_code')} />
                  </label>
                  <label>
                    Country
                    <select className="input" value={propertyForm.country} onChange={onPropertySelectChange('country')} required>
                      <option value="">Select country</option>
                      {COUNTRY_OPTIONS.map((country) => (
                        <option key={country} value={country}>{country}</option>
                      ))}
                    </select>
                  </label>
                  {propertyError && <p className="error">{propertyError}</p>}
                  <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                    <button type="button" className="button secondary small" onClick={() => setShowPropertyModal(false)}>
                      Cancel
                    </button>
                    <button className="button small" disabled={propertySaving}>
                      {propertySaving ? 'Saving...' : 'Save'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
          {showDepartmentModal && (
            <div className="modal-backdrop" onClick={() => setShowDepartmentModal(false)}>
              <div className="modal" onClick={(e) => e.stopPropagation()}>
                <h3>{departmentEditingId ? 'Edit Department' : 'Add Department'}</h3>
                <form onSubmit={onSaveDepartment} style={{ display: 'grid', gap: '12px' }}>
                  <label>
                    Department Name
                    <input
                      className="input"
                      value={departmentForm.name}
                      onChange={onDepartmentChange('name')}
                      required
                    />
                  </label>
                  <label>
                    Property
                    <select className="input" value={departmentForm.property_id} onChange={onDepartmentChange('property_id')}>
                      <option value="">All Properties</option>
                      {propertyList.map((prop) => (
                        <option key={prop.id} value={prop.id}>{prop.name}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Description
                    <textarea
                      className="input"
                      rows={3}
                      value={departmentForm.description}
                      onChange={onDepartmentChange('description')}
                    />
                  </label>
                  {departmentError && <p className="error">{departmentError}</p>}
                  <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                    <button type="button" className="button secondary small" onClick={() => setShowDepartmentModal(false)}>
                      Cancel
                    </button>
                    <button className="button small" disabled={departmentSaving}>
                      {departmentSaving ? 'Saving...' : 'Save'}
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
