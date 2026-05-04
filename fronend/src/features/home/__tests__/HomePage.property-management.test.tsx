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
      userName: 'Property Ops',
      user: {
        id: 10,
        org_id: 3,
        email: 'property.ops@example.com',
        display_name: 'Property Ops',
        permissions,
        is_super_admin: false,
      },
    }),
  )
}

describe('HomePage property management behavior', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('shows property menu item only when user can view/manage properties', async () => {
    setAuth(['properties.view'])
    vi.mocked(apiRequest).mockResolvedValue({ results: [], count: 0 })
    const firstRender = renderWithProviders(<HomePage />, { route: '/home' })

    expect(await screen.findByText('Property Management')).toBeInTheDocument()

    firstRender.unmount()
    localStorage.clear()
    vi.clearAllMocks()
    setAuth([])
    vi.mocked(apiRequest).mockResolvedValue({ results: [], count: 0 })
    renderWithProviders(<HomePage />, { route: '/home' })

    await waitFor(() => {
      expect(screen.queryByText('Property Management')).not.toBeInTheDocument()
    })
  })

  it('maps property list query params including q/page/sort_by/sort_dir', async () => {
    setAuth(['properties.view'])
    vi.mocked(apiRequest).mockImplementation(async (path: string) => {
      if (path.startsWith('/properties?')) {
        return {
          results: [
            {
              id: 21,
              org_id: 3,
              code: 'HTL-001',
              name: 'Hotel One',
              city: 'Boston',
              country: 'United States',
            },
          ],
          count: 25,
        }
      }
      return { results: [], count: 0 }
    })

    renderWithProviders(<HomePage />, { route: '/home' })

    await userEvent.click(await screen.findByRole('button', { name: 'Property Management' }))
    await screen.findByText('Manage properties for this organization.')

    await userEvent.type(screen.getByPlaceholderText('Search properties'), 'hotel')
    await userEvent.click(screen.getByRole('button', { name: 'Search' }))
    await userEvent.click(screen.getByRole('button', { name: /^Code\b/i }))
    await userEvent.click(screen.getByRole('button', { name: 'Next' }))

    await waitFor(() => {
      const calls = vi
        .mocked(apiRequest)
        .mock.calls.filter(([path]) => typeof path === 'string' && path.startsWith('/properties?'))
      expect(calls.length).toBeGreaterThan(0)
      const [lastPath] = calls[calls.length - 1] as [string]
      const params = new URL(`http://localhost${lastPath}`).searchParams
      expect(params.get('org_id')).toBe('3')
      expect(params.get('q')).toBe('hotel')
      expect(params.get('page')).toBe('2')
      expect(params.get('sort_by')).toBe('code')
      expect(params.get('sort_dir')).toBe('asc')
    })
  })

  it('handles property create/edit/delete UI paths and error states', async () => {
    setAuth(['properties.manage'])
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
              timezone: 'Africa/Abidjan',
              address_line1: '123 Main',
              address_line2: '',
              city: 'Boston',
              state: '',
              postal_code: '',
              country: 'United States',
            },
          ],
          count: 1,
        }
      }
      if (path === '/properties' && method === 'POST') {
        return { id: 99, code: 'HTL-002', name: 'Hotel Two' }
      }
      if (path === '/properties/21' && method === 'PATCH') {
        const err = new Error('Property update failed') as Error & { details?: { detail: string } }
        err.details = { detail: 'Property update failed' }
        throw err
      }
      if (path === '/properties/21' && method === 'DELETE') {
        const err = new Error('Property delete failed') as Error & { details?: { detail: string } }
        err.details = { detail: 'Property delete failed' }
        throw err
      }
      return { results: [], count: 0 }
    })

    renderWithProviders(<HomePage />, { route: '/home' })

    await userEvent.click(await screen.findByRole('button', { name: 'Property Management' }))
    await screen.findByText('Manage properties for this organization.')

    expect(screen.getByRole('button', { name: 'Add Property' })).toBeInTheDocument()
    const firstRow = screen.getByText('HTL-001').closest('.list-item') as HTMLElement
    expect(within(firstRow).getByRole('button', { name: 'Edit' })).toBeInTheDocument()
    expect(within(firstRow).getByRole('button', { name: 'Delete' })).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Add Property' }))
    const addHeading = await screen.findByRole('heading', { name: 'Add Property' })
    const addForm = addHeading.closest('.modal')?.querySelector('form') as HTMLFormElement
    await userEvent.type(within(addForm).getByLabelText('Code'), 'HTL-002')
    await userEvent.type(within(addForm).getByLabelText('Name'), 'Hotel Two')
    await userEvent.selectOptions(within(addForm).getByLabelText('Timezone'), 'Africa/Abidjan')
    await userEvent.type(within(addForm).getByLabelText('Address Line 1'), '500 Bay St')
    await userEvent.type(within(addForm).getByLabelText('City'), 'Seattle')
    await userEvent.selectOptions(within(addForm).getByLabelText('Country'), 'United States')
    await userEvent.click(within(addForm).getByRole('button', { name: 'Save' }))

    await waitFor(() => {
      expect(screen.queryByRole('heading', { name: 'Add Property' })).not.toBeInTheDocument()
    })

    const createCalls = vi
      .mocked(apiRequest)
      .mock.calls.filter(([path, opts]) => path === '/properties' && opts?.method === 'POST')
    expect(createCalls.length).toBeGreaterThan(0)
    const [, createOptions] = createCalls[0] as [string, RequestInit]
    expect(JSON.parse(createOptions.body as string)).toMatchObject({
      org_id: 3,
      code: 'HTL-002',
      name: 'Hotel Two',
      timezone: 'Africa/Abidjan',
      city: 'Seattle',
      country: 'United States',
    })

    const refreshedRow = screen.getByText('HTL-001').closest('.list-item') as HTMLElement
    await userEvent.click(within(refreshedRow).getByRole('button', { name: 'Edit' }))
    const editHeading = await screen.findByRole('heading', { name: 'Edit Property' })
    const editForm = editHeading.closest('.modal')?.querySelector('form') as HTMLFormElement
    await userEvent.clear(within(editForm).getByLabelText('Name'))
    await userEvent.type(within(editForm).getByLabelText('Name'), 'Hotel One Updated')
    await userEvent.click(within(editForm).getByRole('button', { name: 'Save' }))

    expect(await within(editForm).findByText('Property update failed')).toBeInTheDocument()

    await userEvent.click(within(editForm).getByRole('button', { name: 'Cancel' }))
    await userEvent.click(screen.getByRole('button', { name: 'Search' }))
    await screen.findByText('HTL-001')
    const latestRow = screen.getByText('HTL-001').closest('.list-item') as HTMLElement
    await userEvent.click(within(latestRow).getByRole('button', { name: 'Delete' }))

    expect(confirmSpy).toHaveBeenCalledWith('Delete this property?')
    expect(await screen.findByText('Property delete failed')).toBeInTheDocument()

    confirmSpy.mockRestore()
  })
})
