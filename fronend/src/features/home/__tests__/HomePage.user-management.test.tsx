import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { HomePage } from '../HomePage'
import { renderWithProviders } from '../../../test/utils'
import { apiRequest } from '../../../shared/api/client'

vi.mock('../../../shared/api/client', () => ({
  apiRequest: vi.fn(),
}))

type UserRow = {
  id: number
  display_name: string
  email: string
  phone?: string
  status: string
  roles?: string[]
}

function setAuth(permissions: string[], options?: { isSuperAdmin?: boolean }) {
  localStorage.setItem(
    'ticketing.auth',
    JSON.stringify({
      accessToken: 'access-token',
      refreshToken: 'refresh-token',
      expiresAt: '2030-01-01T00:00:00Z',
      refreshExpiresAt: '2030-01-10T00:00:00Z',
      userName: 'Ops User',
      user: {
        id: 10,
        org_id: 3,
        email: 'ops@example.com',
        display_name: 'Ops User',
        permissions,
        is_super_admin: options?.isSuperAdmin ?? false,
      },
    }),
  )
}

function installHomePageApiMock(users: UserRow[], options?: { createError?: string; editError?: string }) {
  const createError = options?.createError
  const editError = options?.editError

  vi.mocked(apiRequest).mockImplementation(async (path: string, requestOptions?: RequestInit) => {
    const method = requestOptions?.method || 'GET'
    if (path.startsWith('/users?')) {
      return { results: users, count: 25 }
    }
    if (path.startsWith('/roles?')) {
      return { results: [{ id: 201, name: 'manager' }], count: 1 }
    }
    if (path === '/users' && method === 'POST') {
      if (createError) {
        const err = new Error(createError) as Error & { details?: { detail: string } }
        err.details = { detail: createError }
        throw err
      }
      return { id: 999 }
    }
    if (path.startsWith('/users/') && method === 'PATCH') {
      if (editError) {
        const err = new Error(editError) as Error & { details?: { detail: string } }
        err.details = { detail: editError }
        throw err
      }
      return { id: users[0]?.id ?? 1 }
    }
    if (path.startsWith('/users/') && method === 'DELETE') {
      return null
    }
    if (path.startsWith('/users/') && method === 'POST') {
      return {}
    }
    return { results: [], count: 0 }
  })
}

describe('HomePage user management behavior', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('shows user menu item only when user can view/manage users', async () => {
    setAuth(['users.view'])
    installHomePageApiMock([])
    const firstRender = renderWithProviders(<HomePage />, { route: '/home' })

    expect(await screen.findByText('User Management')).toBeInTheDocument()

    firstRender.unmount()
    localStorage.clear()
    vi.clearAllMocks()
    setAuth([])
    installHomePageApiMock([])
    renderWithProviders(<HomePage />, { route: '/home' })

    await waitFor(() => {
      expect(screen.queryByText('User Management')).not.toBeInTheDocument()
    })
  })

  it('maps user list filters to q/page/sort_by/sort_dir query params', async () => {
    setAuth(['users.view'])
    installHomePageApiMock([
      { id: 1, display_name: 'Alice User', email: 'alice@example.com', status: 'active', roles: [] },
    ])
    renderWithProviders(<HomePage />, { route: '/home' })

    await screen.findByText('User Directory')

    await userEvent.type(screen.getByPlaceholderText('Search users'), 'alice')
    await userEvent.click(screen.getByRole('button', { name: 'Search' }))
    await userEvent.click(screen.getByRole('button', { name: 'Next' }))
    await userEvent.click(screen.getByRole('button', { name: /Email/i }))
    await userEvent.click(screen.getByRole('button', { name: /Email/i }))

    await waitFor(() => {
      const userCalls = vi
        .mocked(apiRequest)
        .mock.calls.filter(([path]) => typeof path === 'string' && path.startsWith('/users?'))
      expect(userCalls.length).toBeGreaterThan(0)
      const [lastPath] = userCalls[userCalls.length - 1] as [string]
      const params = new URL(`http://localhost${lastPath}`).searchParams
      expect(params.get('q')).toBe('alice')
      expect(params.get('page')).toBe('2')
      expect(params.get('sort_by')).toBe('email')
      expect(params.get('sort_dir')).toBe('desc')
    })
  })

  it('submits create modal and renders create error on failure', async () => {
    setAuth(['users.manage'])
    let createAttempt = 0
    vi.mocked(apiRequest).mockImplementation(async (path: string, requestOptions?: RequestInit) => {
      const method = requestOptions?.method || 'GET'
      if (path.startsWith('/users?')) return { results: [], count: 0 }
      if (path.startsWith('/roles?')) return { results: [{ id: 201, name: 'manager' }], count: 1 }
      if (path === '/users' && method === 'POST') {
        createAttempt += 1
        if (createAttempt === 2) {
          const err = new Error('User already exists') as Error & { details?: { detail: string } }
          err.details = { detail: 'User already exists' }
          throw err
        }
        return { id: 321 }
      }
      return { results: [], count: 0 }
    })

    renderWithProviders(<HomePage />, { route: '/home' })

    await userEvent.click(await screen.findByRole('button', { name: 'Add User' }))
    const createModal = await screen.findByRole('heading', { name: 'Add User' })
    const createForm = createModal.closest('.modal')?.querySelector('form') as HTMLFormElement
    const nameInput = within(createForm).getByLabelText('Name')
    const emailInput = within(createForm).getByLabelText('Email')

    await userEvent.type(nameInput, 'Created User')
    await userEvent.type(emailInput, 'created.user@example.com')
    await userEvent.click(within(createForm).getByRole('button', { name: 'Create' }))

    await waitFor(() => {
      expect(screen.queryByRole('heading', { name: 'Add User' })).not.toBeInTheDocument()
    })

    const createCalls = vi
      .mocked(apiRequest)
      .mock.calls.filter(([path, opts]) => path === '/users' && opts?.method === 'POST')
    expect(createCalls.length).toBeGreaterThan(0)
    const [, firstCreateOptions] = createCalls[0] as [string, RequestInit]
    expect(JSON.parse(firstCreateOptions.body as string)).toMatchObject({
      org_id: 3,
      display_name: 'Created User',
      email: 'created.user@example.com',
      status: 'invited',
    })

    await userEvent.click(screen.getByRole('button', { name: 'Add User' }))
    const secondFormTitle = await screen.findByRole('heading', { name: 'Add User' })
    const secondForm = secondFormTitle.closest('.modal')?.querySelector('form') as HTMLFormElement
    await userEvent.type(within(secondForm).getByLabelText('Name'), 'Duplicate User')
    await userEvent.type(within(secondForm).getByLabelText('Email'), 'duplicate.user@example.com')
    await userEvent.click(within(secondForm).getByRole('button', { name: 'Create' }))

    expect(await screen.findByText('User already exists')).toBeInTheDocument()
  })

  it('submits edit modal and renders edit error on failure', async () => {
    setAuth(['users.manage'])
    let patchAttempt = 0
    vi.mocked(apiRequest).mockImplementation(async (path: string, requestOptions?: RequestInit) => {
      const method = requestOptions?.method || 'GET'
      if (path.startsWith('/users?')) {
        return {
          results: [
            {
              id: 22,
              display_name: 'Editable User',
              email: 'editable@example.com',
              status: 'active',
              roles: ['manager'],
            },
          ],
          count: 1,
        }
      }
      if (path.startsWith('/roles?')) return { results: [{ id: 201, name: 'manager' }], count: 1 }
      if (path === '/users/22' && method === 'PATCH') {
        patchAttempt += 1
        if (patchAttempt === 2) {
          const err = new Error('Unable to update user') as Error & { details?: { detail: string } }
          err.details = { detail: 'Unable to update user' }
          throw err
        }
        return { id: 22 }
      }
      return {}
    })

    renderWithProviders(<HomePage />, { route: '/home' })

    await userEvent.click(await screen.findByRole('button', { name: 'Edit' }))
    const editTitle = await screen.findByRole('heading', { name: 'Edit User' })
    const editForm = editTitle.closest('.modal')?.querySelector('form') as HTMLFormElement
    await userEvent.clear(within(editForm).getByLabelText('Name'))
    await userEvent.type(within(editForm).getByLabelText('Name'), 'Updated Name')
    await userEvent.click(within(editForm).getByRole('button', { name: 'Save' }))

    await waitFor(() => {
      expect(screen.queryByText('Edit User')).not.toBeInTheDocument()
    })

    const patchCalls = vi
      .mocked(apiRequest)
      .mock.calls.filter(([path, opts]) => path === '/users/22' && opts?.method === 'PATCH')
    expect(patchCalls.length).toBeGreaterThan(0)
    const [, firstPatchOptions] = patchCalls[0] as [string, RequestInit]
    expect(JSON.parse(firstPatchOptions.body as string)).toMatchObject({
      display_name: 'Updated Name',
      email: 'editable@example.com',
      status: 'active',
    })

    await userEvent.click(screen.getByRole('button', { name: 'Edit' }))
    const secondEditTitle = await screen.findByRole('heading', { name: 'Edit User' })
    const secondEditForm = secondEditTitle.closest('.modal')?.querySelector('form') as HTMLFormElement
    await userEvent.clear(within(secondEditForm).getByLabelText('Name'))
    await userEvent.type(within(secondEditForm).getByLabelText('Name'), 'Broken Update')
    await userEvent.click(within(secondEditForm).getByRole('button', { name: 'Save' }))

    expect(await screen.findByText('Unable to update user')).toBeInTheDocument()
  })

  it('shows invite/suspend/reactivate/delete actions by permission and target role context', async () => {
    setAuth(['users.manage'])
    installHomePageApiMock([
      { id: 1, display_name: 'Invited User', email: 'invited@example.com', status: 'invited', roles: ['staff'] },
      { id: 2, display_name: 'Active User', email: 'active@example.com', status: 'active', roles: ['staff'] },
      { id: 3, display_name: 'Suspended User', email: 'suspended@example.com', status: 'suspended', roles: ['staff'] },
      { id: 4, display_name: 'Super Admin User', email: 'super@example.com', status: 'active', roles: ['super admin'] },
    ])
    renderWithProviders(<HomePage />, { route: '/home' })

    await screen.findByText('Invited User')

    const invitedRow = screen.getByText('Invited User').closest('.list-item') as HTMLElement
    const activeRow = screen.getByText('Active User').closest('.list-item') as HTMLElement
    const suspendedRow = screen.getByText('Suspended User').closest('.list-item') as HTMLElement
    const superRow = screen.getByText('Super Admin User').closest('.list-item') as HTMLElement

    expect(within(invitedRow).getByRole('button', { name: 'Resend Invite' })).toBeInTheDocument()
    expect(within(invitedRow).getByRole('button', { name: 'Delete' })).toBeInTheDocument()
    expect(within(activeRow).getByRole('button', { name: 'Suspend' })).toBeInTheDocument()
    expect(within(activeRow).getByRole('button', { name: 'Delete' })).toBeInTheDocument()
    expect(within(suspendedRow).getByRole('button', { name: 'Reactivate' })).toBeInTheDocument()
    expect(within(suspendedRow).getByRole('button', { name: 'Delete' })).toBeInTheDocument()
    expect(within(superRow).getByRole('button', { name: 'Suspend' })).toBeInTheDocument()
    expect(within(superRow).queryByRole('button', { name: 'Delete' })).not.toBeInTheDocument()
  })
})
