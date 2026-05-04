import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { HomePage } from '../HomePage'
import { renderWithProviders } from '../../../test/utils'
import { apiRequest } from '../../../shared/api/client'

vi.mock('../../../shared/api/client', () => ({
  apiRequest: vi.fn(),
}))

function setAuth(permissions: string[]) {
  localStorage.setItem(
    'ticketing.auth',
    JSON.stringify({
      accessToken: 'access-token',
      refreshToken: 'refresh-token',
      expiresAt: '2030-01-01T00:00:00Z',
      refreshExpiresAt: '2030-01-10T00:00:00Z',
      userName: 'Role Ops',
      user: {
        id: 10,
        org_id: 3,
        email: 'role.ops@example.com',
        display_name: 'Role Ops',
        permissions,
        is_super_admin: false,
      },
    }),
  )
}

describe('HomePage role management behavior', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('shows role menu item only when user can view/manage roles', async () => {
    setAuth(['roles.view'])
    vi.mocked(apiRequest).mockResolvedValue({ results: [], count: 0 })
    const firstRender = renderWithProviders(<HomePage />, { route: '/home' })

    expect(await screen.findByText('Role Management')).toBeInTheDocument()

    firstRender.unmount()
    localStorage.clear()
    vi.clearAllMocks()
    setAuth([])
    vi.mocked(apiRequest).mockResolvedValue({ results: [], count: 0 })
    renderWithProviders(<HomePage />, { route: '/home' })

    await waitFor(() => {
      expect(screen.queryByText('Role Management')).not.toBeInTheDocument()
    })
  })

  it('maps role list sorting and pagination to query params', async () => {
    setAuth(['roles.view'])
    vi.mocked(apiRequest).mockImplementation(async (path: string) => {
      if (path.startsWith('/roles?')) {
        return {
          results: [{ id: 11, name: 'frontdesk', description: '' }],
          count: 25,
        }
      }
      return { results: [], count: 0 }
    })

    renderWithProviders(<HomePage />, { route: '/home' })

    await userEvent.click(await screen.findByRole('button', { name: 'Role Management' }))
    await screen.findByText('Create and manage roles.')

    await userEvent.click(screen.getByRole('button', { name: /Created/i }))
    await userEvent.click(screen.getByRole('button', { name: /Created/i }))
    await userEvent.click(screen.getByRole('button', { name: 'Next' }))

    await waitFor(() => {
      const roleCalls = vi
        .mocked(apiRequest)
        .mock.calls.filter(([path]) => typeof path === 'string' && path.startsWith('/roles?'))
      expect(roleCalls.length).toBeGreaterThan(0)
      const [lastPath] = roleCalls[roleCalls.length - 1] as [string]
      const params = new URL(`http://localhost${lastPath}`).searchParams
      expect(params.get('org_id')).toBe('3')
      expect(params.get('page')).toBe('2')
      expect(params.get('sort_by')).toBe('created_at')
      expect(params.get('sort_dir')).toBe('desc')
    })
  })

  it('handles role create/edit/delete actions with expected UI states', async () => {
    setAuth(['roles.manage'])
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

    vi.mocked(apiRequest).mockImplementation(async (path: string, options?: RequestInit) => {
      const method = options?.method || 'GET'
      if (path.startsWith('/roles?')) {
        return {
          results: [{ id: 11, name: 'frontdesk', description: 'Front desk role' }],
          count: 1,
        }
      }
      if (path === '/roles' && method === 'POST') {
        return { id: 44, org_id: 3, name: 'supervisor', description: 'Shift supervisor' }
      }
      if (path === '/roles/11' && method === 'PATCH') {
        const err = new Error('Role update failed') as Error & { details?: { detail: string } }
        err.details = { detail: 'Role update failed' }
        throw err
      }
      if (path === '/roles/11' && method === 'DELETE') {
        const err = new Error('Role is in use') as Error & { details?: { detail: string } }
        err.details = { detail: 'Role is in use' }
        throw err
      }
      return { results: [], count: 0 }
    })

    renderWithProviders(<HomePage />, { route: '/home' })

    await userEvent.click(await screen.findByRole('button', { name: 'Role Management' }))
    await screen.findByText('Create and manage roles.')

    expect(screen.getByRole('button', { name: 'Add Role' })).toBeInTheDocument()
    const initialRoleRow = screen.getByText('frontdesk').closest('.list-item') as HTMLElement
    expect(within(initialRoleRow).getByRole('button', { name: 'Edit' })).toBeInTheDocument()
    expect(within(initialRoleRow).getByRole('button', { name: 'Delete' })).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Add Role' }))
    const addRoleHeading = await screen.findByRole('heading', { name: 'Add Role' })
    const addRoleForm = addRoleHeading.closest('.modal')?.querySelector('form') as HTMLFormElement
    await userEvent.type(within(addRoleForm).getByLabelText('Name'), 'supervisor')
    await userEvent.type(within(addRoleForm).getByLabelText('Description'), 'Shift supervisor')
    await userEvent.click(within(addRoleForm).getByRole('button', { name: 'Save' }))

    await waitFor(() => {
      expect(screen.queryByRole('heading', { name: 'Add Role' })).not.toBeInTheDocument()
    })

    const createCalls = vi
      .mocked(apiRequest)
      .mock.calls.filter(([path, opts]) => path === '/roles' && opts?.method === 'POST')
    expect(createCalls.length).toBeGreaterThan(0)
    const [, createOptions] = createCalls[0] as [string, RequestInit]
    expect(JSON.parse(createOptions.body as string)).toMatchObject({
      org_id: 3,
      name: 'supervisor',
      description: 'Shift supervisor',
    })

    const refreshedRoleRow = screen.getByText('frontdesk').closest('.list-item') as HTMLElement
    await userEvent.click(within(refreshedRoleRow).getByRole('button', { name: 'Edit' }))
    const editRoleHeading = await screen.findByRole('heading', { name: 'Edit Role' })
    const editRoleForm = editRoleHeading.closest('.modal')?.querySelector('form') as HTMLFormElement
    await userEvent.clear(within(editRoleForm).getByLabelText('Description'))
    await userEvent.type(within(editRoleForm).getByLabelText('Description'), 'Updated description')
    await userEvent.click(within(editRoleForm).getByRole('button', { name: 'Save' }))

    expect(await within(editRoleForm).findByText('Role update failed')).toBeInTheDocument()

    await userEvent.click(within(editRoleForm).getByRole('button', { name: 'Cancel' }))
    await userEvent.click(screen.getByRole('button', { name: 'Search' }))
    await screen.findByText('frontdesk')
    const latestRoleRow = screen.getByText('frontdesk').closest('.list-item') as HTMLElement
    await userEvent.click(within(latestRoleRow).getByRole('button', { name: 'Delete' }))

    expect(confirmSpy).toHaveBeenCalledWith('Delete this role?')
    expect(await screen.findByText('Role is in use')).toBeInTheDocument()

    confirmSpy.mockRestore()
  })
})
