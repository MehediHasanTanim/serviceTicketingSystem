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
      userName: 'Org Ops',
      user: {
        id: 10,
        org_id: 3,
        email: 'org.ops@example.com',
        display_name: 'Org Ops',
        permissions,
        is_super_admin: false,
      },
    }),
  )
}

describe('HomePage organization management behavior', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('shows organization menu item only when user can view/manage organizations', async () => {
    setAuth(['org.view'])
    vi.mocked(apiRequest).mockResolvedValue({ results: [], count: 0 })
    const firstRender = renderWithProviders(<HomePage />, { route: '/home' })
    expect(await screen.findByText('Organization Management')).toBeInTheDocument()

    firstRender.unmount()
    localStorage.clear()
    vi.clearAllMocks()
    setAuth([])
    vi.mocked(apiRequest).mockResolvedValue({ results: [], count: 0 })
    renderWithProviders(<HomePage />, { route: '/home' })

    await waitFor(() => {
      expect(screen.queryByText('Organization Management')).not.toBeInTheDocument()
    })
  })

  it('maps organization list query/sort/pagination params', async () => {
    setAuth(['org.view'])
    vi.mocked(apiRequest).mockImplementation(async (path: string) => {
      if (path.startsWith('/organizations?')) {
        return {
          results: [{ id: 7, name: 'Northwind', legal_name: 'Northwind LLC', status: 'active' }],
          count: 25,
        }
      }
      return { results: [], count: 0 }
    })

    renderWithProviders(<HomePage />, { route: '/home' })
    await userEvent.click(await screen.findByRole('button', { name: 'Organization Management' }))
    await screen.findByText('Manage organizations.')

    await userEvent.type(screen.getByPlaceholderText('Search organizations'), 'north')
    await userEvent.click(screen.getByRole('button', { name: 'Search' }))
    await userEvent.click(screen.getByRole('button', { name: /^Name\b/i }))
    await userEvent.click(screen.getByRole('button', { name: /^Name\b/i }))
    await userEvent.click(screen.getByRole('button', { name: 'Next' }))

    await waitFor(() => {
      const calls = vi
        .mocked(apiRequest)
        .mock.calls.filter(([path]) => typeof path === 'string' && path.startsWith('/organizations?'))
      expect(calls.length).toBeGreaterThan(0)
      const [lastPath] = calls[calls.length - 1] as [string]
      const params = new URL(`http://localhost${lastPath}`).searchParams
      expect(params.get('q')).toBe('north')
      expect(params.get('page')).toBe('2')
      expect(params.get('sort_by')).toBe('name')
      expect(params.get('sort_dir')).toBe('desc')
    })
  })

  it('covers organization create/edit/delete UI paths and errors', async () => {
    setAuth(['org.manage'])
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

    vi.mocked(apiRequest).mockImplementation(async (path: string, options?: RequestInit) => {
      const method = options?.method || 'GET'
      if (path.startsWith('/organizations?')) {
        return {
          results: [{ id: 7, name: 'Northwind', legal_name: 'Northwind LLC', status: 'active' }],
          count: 1,
        }
      }
      if (path === '/organizations' && method === 'POST') {
        return { id: 8, name: 'Globex', legal_name: 'Globex LLC', status: 'active' }
      }
      if (path === '/organizations/7' && method === 'PATCH') {
        const err = new Error('Organization update failed') as Error & { details?: { detail: string } }
        err.details = { detail: 'Organization update failed' }
        throw err
      }
      if (path === '/organizations/7' && method === 'DELETE') {
        const err = new Error('Organization delete failed') as Error & { details?: { detail: string } }
        err.details = { detail: 'Organization delete failed' }
        throw err
      }
      return { results: [], count: 0 }
    })

    renderWithProviders(<HomePage />, { route: '/home' })
    await userEvent.click(await screen.findByRole('button', { name: 'Organization Management' }))
    await screen.findByText('Manage organizations.')

    expect(screen.getByRole('button', { name: 'Add Organization' })).toBeInTheDocument()
    const firstRow = screen.getByText('Northwind').closest('.list-item') as HTMLElement
    expect(within(firstRow).getByRole('button', { name: 'Edit' })).toBeInTheDocument()
    expect(within(firstRow).getByRole('button', { name: 'Delete' })).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Add Organization' }))
    const addHeading = await screen.findByRole('heading', { name: 'Add Organization' })
    const addForm = addHeading.closest('.modal')?.querySelector('form') as HTMLFormElement
    await userEvent.type(within(addForm).getByLabelText('Name'), 'Globex')
    await userEvent.type(within(addForm).getByLabelText('Legal Name'), 'Globex LLC')
    await userEvent.click(within(addForm).getByRole('button', { name: 'Save' }))

    await waitFor(() => {
      expect(screen.queryByRole('heading', { name: 'Add Organization' })).not.toBeInTheDocument()
    })

    const createCalls = vi
      .mocked(apiRequest)
      .mock.calls.filter(([path, opts]) => path === '/organizations' && opts?.method === 'POST')
    expect(createCalls.length).toBeGreaterThan(0)
    const [, createOptions] = createCalls[0] as [string, RequestInit]
    expect(JSON.parse(createOptions.body as string)).toMatchObject({
      name: 'Globex',
      legal_name: 'Globex LLC',
      status: 'active',
    })

    const refreshedRow = screen.getByText('Northwind').closest('.list-item') as HTMLElement
    await userEvent.click(within(refreshedRow).getByRole('button', { name: 'Edit' }))
    const editHeading = await screen.findByRole('heading', { name: 'Edit Organization' })
    const editForm = editHeading.closest('.modal')?.querySelector('form') as HTMLFormElement
    await userEvent.clear(within(editForm).getByLabelText('Legal Name'))
    await userEvent.type(within(editForm).getByLabelText('Legal Name'), 'Northwind Holdings LLC')
    await userEvent.click(within(editForm).getByRole('button', { name: 'Save' }))
    expect(await within(editForm).findByText('Organization update failed')).toBeInTheDocument()

    await userEvent.click(within(editForm).getByRole('button', { name: 'Cancel' }))
    await userEvent.click(screen.getByRole('button', { name: 'Search' }))
    await screen.findByText('Northwind')
    const latestRow = screen.getByText('Northwind').closest('.list-item') as HTMLElement
    await userEvent.click(within(latestRow).getByRole('button', { name: 'Delete' }))

    expect(confirmSpy).toHaveBeenCalledWith('Delete this organization?')
    expect(await screen.findByText('Organization delete failed')).toBeInTheDocument()
    confirmSpy.mockRestore()
  })
})
