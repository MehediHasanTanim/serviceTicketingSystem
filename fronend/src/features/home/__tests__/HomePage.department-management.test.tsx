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
      userName: 'Department Ops',
      user: {
        id: 10,
        org_id: 3,
        email: 'department.ops@example.com',
        display_name: 'Department Ops',
        permissions,
        is_super_admin: false,
      },
    }),
  )
}

describe('HomePage department management behavior', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('shows department menu item only when user can view/manage departments', async () => {
    setAuth(['departments.view'])
    vi.mocked(apiRequest).mockResolvedValue({ results: [], count: 0 })
    const firstRender = renderWithProviders(<HomePage />, { route: '/home' })

    expect(await screen.findByText('Department Management')).toBeInTheDocument()

    firstRender.unmount()
    localStorage.clear()
    vi.clearAllMocks()
    setAuth([])
    vi.mocked(apiRequest).mockResolvedValue({ results: [], count: 0 })
    renderWithProviders(<HomePage />, { route: '/home' })

    await waitFor(() => {
      expect(screen.queryByText('Department Management')).not.toBeInTheDocument()
    })
  })

  it('maps department list query params including q/page/sort_by/sort_dir', async () => {
    setAuth(['departments.view'])
    vi.mocked(apiRequest).mockImplementation(async (path: string) => {
      if (path.startsWith('/departments?')) {
        return {
          results: [{ id: 31, org_id: 3, property_id: 21, name: 'Front Office', description: 'Desk team' }],
          count: 25,
        }
      }
      if (path.startsWith('/properties?')) {
        return {
          results: [{ id: 21, name: 'Hotel One', code: 'HTL-001', city: 'Boston', country: 'United States' }],
          count: 1,
        }
      }
      return { results: [], count: 0 }
    })

    renderWithProviders(<HomePage />, { route: '/home' })

    await userEvent.click(await screen.findByRole('button', { name: 'Department Management' }))
    await screen.findByText('Manage departments for this organization.')

    await userEvent.type(screen.getByPlaceholderText('Search departments'), 'front')
    await userEvent.click(screen.getByRole('button', { name: 'Search' }))
    await userEvent.click(screen.getByRole('button', { name: /^Name\b/i }))
    await userEvent.click(screen.getByRole('button', { name: 'Next' }))

    await waitFor(() => {
      const calls = vi
        .mocked(apiRequest)
        .mock.calls.filter(([path]) => typeof path === 'string' && path.startsWith('/departments?'))
      expect(calls.length).toBeGreaterThan(0)
      const [lastPath] = calls[calls.length - 1] as [string]
      const params = new URL(`http://localhost${lastPath}`).searchParams
      expect(params.get('org_id')).toBe('3')
      expect(params.get('q')).toBe('front')
      expect(params.get('page')).toBe('2')
      expect(params.get('sort_by')).toBe('name')
      expect(params.get('sort_dir')).toBe('desc')
    })
  })

  it('handles department create/edit/delete UI paths and error states', async () => {
    setAuth(['departments.manage'])
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

    vi.mocked(apiRequest).mockImplementation(async (path: string, options?: RequestInit) => {
      const method = options?.method || 'GET'
      if (path.startsWith('/properties?')) {
        return {
          results: [
            {
              id: 21,
              org_id: 3,
              code: 'HTL-001',
              name: 'Hotel One',
              timezone: 'UTC',
              address_line1: '123 Main',
              city: 'Boston',
              country: 'United States',
            },
          ],
          count: 1,
        }
      }
      if (path.startsWith('/departments?')) {
        return {
          results: [{ id: 31, org_id: 3, property_id: 21, name: 'Front Office', description: 'Desk team' }],
          count: 1,
        }
      }
      if (path === '/departments' && method === 'POST') {
        return { id: 44, org_id: 3, property_id: 21, name: 'Security', description: 'Security team' }
      }
      if (path === '/departments/31' && method === 'PATCH') {
        const err = new Error('Department update failed') as Error & { details?: { detail: string } }
        err.details = { detail: 'Department update failed' }
        throw err
      }
      if (path === '/departments/31' && method === 'DELETE') {
        const err = new Error('Department delete failed') as Error & { details?: { detail: string } }
        err.details = { detail: 'Department delete failed' }
        throw err
      }
      return { results: [], count: 0 }
    })

    renderWithProviders(<HomePage />, { route: '/home' })

    await userEvent.click(await screen.findByRole('button', { name: 'Department Management' }))
    await screen.findByText('Manage departments for this organization.')

    expect(screen.getByRole('button', { name: 'Add Department' })).toBeInTheDocument()
    const firstRow = screen.getByText('Front Office').closest('.list-item') as HTMLElement
    expect(within(firstRow).getByRole('button', { name: 'Edit' })).toBeInTheDocument()
    expect(within(firstRow).getByRole('button', { name: 'Delete' })).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Add Department' }))
    const addHeading = await screen.findByRole('heading', { name: 'Add Department' })
    const addForm = addHeading.closest('.modal')?.querySelector('form') as HTMLFormElement
    await userEvent.type(within(addForm).getByLabelText('Department Name'), 'Security')
    await userEvent.selectOptions(within(addForm).getByLabelText('Property'), '21')
    await userEvent.type(within(addForm).getByLabelText('Description'), 'Security team')
    await userEvent.click(within(addForm).getByRole('button', { name: 'Save' }))

    await waitFor(() => {
      expect(screen.queryByRole('heading', { name: 'Add Department' })).not.toBeInTheDocument()
    })

    const createCalls = vi
      .mocked(apiRequest)
      .mock.calls.filter(([path, opts]) => path === '/departments' && opts?.method === 'POST')
    expect(createCalls.length).toBeGreaterThan(0)
    const [, createOptions] = createCalls[0] as [string, RequestInit]
    expect(JSON.parse(createOptions.body as string)).toMatchObject({
      org_id: 3,
      property_id: 21,
      name: 'Security',
      description: 'Security team',
    })

    const refreshedRow = screen.getByText('Front Office').closest('.list-item') as HTMLElement
    await userEvent.click(within(refreshedRow).getByRole('button', { name: 'Edit' }))
    const editHeading = await screen.findByRole('heading', { name: 'Edit Department' })
    const editForm = editHeading.closest('.modal')?.querySelector('form') as HTMLFormElement
    await userEvent.clear(within(editForm).getByLabelText('Description'))
    await userEvent.type(within(editForm).getByLabelText('Description'), 'Updated desk team')
    await userEvent.click(within(editForm).getByRole('button', { name: 'Save' }))

    expect(await within(editForm).findByText('Department update failed')).toBeInTheDocument()

    await userEvent.click(within(editForm).getByRole('button', { name: 'Cancel' }))
    await userEvent.click(screen.getByRole('button', { name: 'Search' }))
    await screen.findByText('Front Office')
    const latestRow = screen.getByText('Front Office').closest('.list-item') as HTMLElement
    await userEvent.click(within(latestRow).getByRole('button', { name: 'Delete' }))

    expect(confirmSpy).toHaveBeenCalledWith('Delete this department?')
    expect(await screen.findByText('Department delete failed')).toBeInTheDocument()

    confirmSpy.mockRestore()
  })
})
