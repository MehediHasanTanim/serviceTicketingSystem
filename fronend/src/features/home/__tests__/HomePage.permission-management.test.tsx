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
      userName: 'Perm Ops',
      user: {
        id: 10,
        org_id: 3,
        email: 'perm.ops@example.com',
        display_name: 'Perm Ops',
        permissions,
        is_super_admin: false,
      },
    }),
  )
}

describe('HomePage permission management behavior', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('shows permission menu item only when user can view/manage permissions', async () => {
    setAuth(['permissions.view'])
    vi.mocked(apiRequest).mockResolvedValue({ results: [], count: 0 })
    const firstRender = renderWithProviders(<HomePage />, { route: '/home' })

    expect(await screen.findByText('Permission Management')).toBeInTheDocument()

    firstRender.unmount()
    localStorage.clear()
    vi.clearAllMocks()
    setAuth([])
    vi.mocked(apiRequest).mockResolvedValue({ results: [], count: 0 })
    renderWithProviders(<HomePage />, { route: '/home' })

    await waitFor(() => {
      expect(screen.queryByText('Permission Management')).not.toBeInTheDocument()
    })
  })

  it('maps permission list query params including q/page/sort_by/sort_dir', async () => {
    setAuth(['permissions.view'])
    vi.mocked(apiRequest).mockImplementation(async (path: string) => {
      if (path.startsWith('/permissions?')) {
        return {
          results: [{ id: 21, code: 'users.view', description: 'View users' }],
          count: 25,
        }
      }
      return { results: [], count: 0 }
    })

    renderWithProviders(<HomePage />, { route: '/home' })

    await userEvent.click(await screen.findByRole('button', { name: 'Permission Management' }))
    await screen.findByText('Define and manage permissions.')

    await userEvent.type(screen.getByPlaceholderText('Search permissions'), 'user')
    await userEvent.click(screen.getByRole('button', { name: 'Search' }))
    await userEvent.click(screen.getByRole('button', { name: /Code/i }))
    await userEvent.click(screen.getByRole('button', { name: 'Next' }))

    await waitFor(() => {
      const calls = vi
        .mocked(apiRequest)
        .mock.calls.filter(([path]) => typeof path === 'string' && path.startsWith('/permissions?'))
      expect(calls.length).toBeGreaterThan(0)
      const [lastPath] = calls[calls.length - 1] as [string]
      const params = new URL(`http://localhost${lastPath}`).searchParams
      expect(params.get('q')).toBe('user')
      expect(params.get('page')).toBe('2')
      expect(params.get('sort_by')).toBe('code')
      expect(params.get('sort_dir')).toBe('desc')
    })
  })

  it('handles permission create/edit/delete UI paths and error states', async () => {
    setAuth(['permissions.manage'])
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

    vi.mocked(apiRequest).mockImplementation(async (path: string, options?: RequestInit) => {
      const method = options?.method || 'GET'
      if (path.startsWith('/permissions?')) {
        return {
          results: [{ id: 21, code: 'users.view', description: 'View users' }],
          count: 1,
        }
      }
      if (path === '/permissions' && method === 'POST') {
        return { id: 33, code: 'tickets.manage', description: 'Manage tickets' }
      }
      if (path === '/permissions/21' && method === 'PATCH') {
        const err = new Error('Permission already exists') as Error & { details?: { detail: string } }
        err.details = { detail: 'Permission already exists' }
        throw err
      }
      if (path === '/permissions/21' && method === 'DELETE') {
        const err = new Error('Permission is in use') as Error & { details?: { detail: string } }
        err.details = { detail: 'Permission is in use' }
        throw err
      }
      return { results: [], count: 0 }
    })

    renderWithProviders(<HomePage />, { route: '/home' })

    await userEvent.click(await screen.findByRole('button', { name: 'Permission Management' }))
    await screen.findByText('Define and manage permissions.')

    expect(screen.getByRole('button', { name: 'Add Permission' })).toBeInTheDocument()
    const firstRow = screen.getByText('users.view').closest('.list-item') as HTMLElement
    expect(within(firstRow).getByRole('button', { name: 'Edit' })).toBeInTheDocument()
    expect(within(firstRow).getByRole('button', { name: 'Delete' })).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Add Permission' }))
    const addModalHeading = await screen.findByRole('heading', { name: 'Add Permission' })
    const addForm = addModalHeading.closest('.modal')?.querySelector('form') as HTMLFormElement
    await userEvent.type(within(addForm).getByLabelText('Code'), 'tickets.manage')
    await userEvent.type(within(addForm).getByLabelText('Description'), 'Manage tickets')
    await userEvent.click(within(addForm).getByRole('button', { name: 'Save' }))

    await waitFor(() => {
      expect(screen.queryByRole('heading', { name: 'Add Permission' })).not.toBeInTheDocument()
    })

    const createCalls = vi
      .mocked(apiRequest)
      .mock.calls.filter(([path, opts]) => path === '/permissions' && opts?.method === 'POST')
    expect(createCalls.length).toBeGreaterThan(0)
    const [, createOptions] = createCalls[0] as [string, RequestInit]
    expect(JSON.parse(createOptions.body as string)).toMatchObject({
      code: 'tickets.manage',
      description: 'Manage tickets',
    })

    const refreshedRow = screen.getByText('users.view').closest('.list-item') as HTMLElement
    await userEvent.click(within(refreshedRow).getByRole('button', { name: 'Edit' }))
    const editModalHeading = await screen.findByRole('heading', { name: 'Edit Permission' })
    const editForm = editModalHeading.closest('.modal')?.querySelector('form') as HTMLFormElement
    await userEvent.clear(within(editForm).getByLabelText('Description'))
    await userEvent.type(within(editForm).getByLabelText('Description'), 'Updated users view')
    await userEvent.click(within(editForm).getByRole('button', { name: 'Save' }))

    expect(await within(editForm).findByText('Permission already exists')).toBeInTheDocument()

    await userEvent.click(within(editForm).getByRole('button', { name: 'Cancel' }))
    await userEvent.click(screen.getByRole('button', { name: 'Search' }))
    await screen.findByText('users.view')
    const latestRow = screen.getByText('users.view').closest('.list-item') as HTMLElement
    await userEvent.click(within(latestRow).getByRole('button', { name: 'Delete' }))

    expect(confirmSpy).toHaveBeenCalledWith('Delete this permission?')
    expect(await screen.findByText('Permission is in use')).toBeInTheDocument()

    confirmSpy.mockRestore()
  })
})
