import { screen, waitFor } from '@testing-library/react'
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
      userName: 'Ops User',
      user: {
        id: 10,
        org_id: 3,
        email: 'ops@example.com',
        display_name: 'Ops User',
        permissions,
        is_super_admin: false,
      },
    }),
  )
}

describe('HomePage role visibility and audit filters', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
    vi.mocked(apiRequest).mockImplementation(async (path: string) => {
      if (path.startsWith('/users?')) return { results: [], count: 0 }
      if (path.startsWith('/audit-logs?')) return { results: [], count: 0 }
      return { results: [], count: 0 }
    })
  })

  it('shows only permitted management menu items', async () => {
    setAuth(['audit.view'])
    renderWithProviders(<HomePage />, { route: '/home' })

    expect(await screen.findByText('Audit Logs')).toBeInTheDocument()
    expect(screen.queryByText('User Management')).not.toBeInTheDocument()
    expect(screen.queryByText('Role Management')).not.toBeInTheDocument()
    expect(screen.queryByText('Permission Management')).not.toBeInTheDocument()
  })

  it('maps audit filter inputs to audit-logs query parameters', async () => {
    setAuth(['users.view', 'audit.view'])
    const { container } = renderWithProviders(<HomePage />, { route: '/home' })

    await userEvent.click(await screen.findByRole('button', { name: 'Audit Logs' }))

    await userEvent.type(screen.getByPlaceholderText('Search logs'), 'login')
    await userEvent.type(screen.getByPlaceholderText('Actor ID'), '77')
    await userEvent.type(screen.getByPlaceholderText('Action'), 'user.created')
    await userEvent.type(screen.getByPlaceholderText('Target type'), 'user')

    const dateInputs = container.querySelectorAll('input[type="date"]')
    if (dateInputs.length >= 2) {
      await userEvent.type(dateInputs[0], '2026-04-01')
      await userEvent.type(dateInputs[1], '2026-04-22')
    }

    await userEvent.click(screen.getByRole('button', { name: 'Search' }))

    await waitFor(() => {
      const auditCalls = vi
        .mocked(apiRequest)
        .mock.calls.filter(([path]) => typeof path === 'string' && path.startsWith('/audit-logs?'))
      expect(auditCalls.length).toBeGreaterThan(0)
    })

    const auditCalls = vi
      .mocked(apiRequest)
      .mock.calls.filter(([path]) => typeof path === 'string' && path.startsWith('/audit-logs?'))
    const [lastPath] = auditCalls[auditCalls.length - 1] as [string]
    const params = new URL(`http://localhost${lastPath}`).searchParams

    expect(params.get('org_id')).toBe('3')
    expect(params.get('q')).toBe('login')
    expect(params.get('actor_user_id')).toBe('77')
    expect(params.get('action')).toBe('user.created')
    expect(params.get('target_type')).toBe('user')
    expect(params.get('date_from')).toBe('2026-04-01')
    expect(params.get('date_to')).toBe('2026-04-22')
    expect(params.get('sort_by')).toBe('created_at')
    expect(params.get('sort_dir')).toBe('desc')
  })

  it('maps audit sort toggles and pagination controls to query parameters', async () => {
    setAuth(['audit.view'])
    vi.mocked(apiRequest).mockImplementation(async (path: string) => {
      if (path.startsWith('/audit-logs?')) {
        return {
          results: [{ id: 1, action: 'user.created', target_type: 'user', target_id: '55', created_at: '2026-04-21T10:00:00Z' }],
          count: 25,
        }
      }
      return { results: [], count: 0 }
    })

    renderWithProviders(<HomePage />, { route: '/home' })
    await userEvent.click(await screen.findByRole('button', { name: 'Audit Logs' }))
    await screen.findByText('Search and review recent activity across your organization.')

    await userEvent.click(screen.getByRole('button', { name: /^Action\b/i }))
    await userEvent.click(screen.getByRole('button', { name: /^Action\b/i }))
    await userEvent.click(screen.getByRole('button', { name: 'Next' }))

    await waitFor(() => {
      const auditCalls = vi
        .mocked(apiRequest)
        .mock.calls.filter(([path]) => typeof path === 'string' && path.startsWith('/audit-logs?'))
      expect(auditCalls.length).toBeGreaterThan(0)
      const [lastPath] = auditCalls[auditCalls.length - 1] as [string]
      const params = new URL(`http://localhost${lastPath}`).searchParams
      expect(params.get('org_id')).toBe('3')
      expect(params.get('page')).toBe('2')
      expect(params.get('sort_by')).toBe('action')
      expect(params.get('sort_dir')).toBe('desc')
    })
  })
})
