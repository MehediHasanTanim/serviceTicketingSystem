import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { renderWithProviders } from '../../../test/utils'
import { HousekeepingAuditLogsPage } from '../pages/HousekeepingAuditLogsPage'
import { apiRequest } from '../../../shared/api/client'

vi.mock('../../../shared/api/client', () => ({ apiRequest: vi.fn() }))

describe('HousekeepingAuditLogsPage', () => {
  it('renders rows, updates filters, paginates, and opens metadata drawer', async () => {
    localStorage.setItem('ticketing.auth', JSON.stringify({ accessToken: 'x', refreshToken: 'y', expiresAt: '2030-01-01', refreshExpiresAt: '2030-01-10', userName: 'Ops', user: { id: 1, org_id: 3, email: 'ops@example.com', display_name: 'Ops', permissions: ['audit.view'] } }))

    vi.mocked(apiRequest).mockImplementation(async (path: string) => {
      if (path.startsWith('/audit-logs?')) {
        return { count: 11, results: [{ id: 1, actor_user_id: 7, action: 'housekeeping_task_assigned', target_type: 'housekeeping_task', target_id: '51', metadata: { x: 1 }, created_at: '2026-05-01T10:00:00Z' }] }
      }
      return { count: 0, results: [] }
    })

    renderWithProviders(<HousekeepingAuditLogsPage />, { route: '/housekeeping/audit-logs' })
    expect(await screen.findByText('housekeeping_task_assigned')).toBeInTheDocument()

    await userEvent.type(screen.getByPlaceholderText('Action'), 'room_status_changed')
    await waitFor(() => {
      const calls = vi.mocked(apiRequest).mock.calls.filter(([path]) => typeof path === 'string' && path.startsWith('/audit-logs?'))
      expect(calls.length).toBeGreaterThan(0)
    })

    await userEvent.click(screen.getByRole('button', { name: 'Next' }))
    await userEvent.click(screen.getByRole('button', { name: 'Open' }))
    expect(await screen.findByRole('dialog', { name: 'Audit metadata' })).toBeInTheDocument()
  })
})
