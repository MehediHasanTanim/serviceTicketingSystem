import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../../shared/api/client'
import { renderWithProviders } from '../../../test/utils'
import { FBAuditLogsPage } from '../pages/FBAuditLogsPage'

vi.mock('../../../shared/api/client', () => ({ apiRequest: vi.fn() }))

describe('FBAuditLogsPage', () => {
  it('renders events and opens metadata drawer and paginates', async () => {
    localStorage.setItem('ticketing.auth', JSON.stringify({ accessToken: 'x', refreshToken: 'y', expiresAt: '2030-01-01', refreshExpiresAt: '2030-01-10', userName: 'Ops', user: { id: 1, org_id: 5, email: 'ops@example.com', display_name: 'Ops', permissions: ['audit.view'] } }))
    vi.mocked(apiRequest).mockImplementation(async (path: string) => {
      if (path.startsWith('/food-beverage/audit-logs?')) return { count: 11, results: [{ id: 1, created_at: '2026-05-01T10:00:00Z', actor_user_id: 7, action: 'fb_task_assigned', target_type: 'fb_task', target_id: '9', metadata: { reason: 'rebalance' } }] }
      return { count: 0, results: [] }
    })
    renderWithProviders(<FBAuditLogsPage />, { route: '/food-beverage/audit-logs' })
    expect(await screen.findByText('fb_task_assigned')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Open' }))
    expect(await screen.findByRole('dialog', { name: 'Audit metadata' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Next' }))
    expect(screen.getByText('Page 2 of 2')).toBeInTheDocument()
  })
})
