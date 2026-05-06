import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../../shared/api/client'
import { renderWithProviders } from '../../../test/utils'
import { FBDashboardPage } from '../pages/FBDashboardPage'

vi.mock('../../../shared/api/client', () => ({ apiRequest: vi.fn() }))

describe('FBDashboardPage', () => {
  it('renders KPI cards, zero-safe values, query filters and chart rows', async () => {
    localStorage.setItem('ticketing.auth', JSON.stringify({ accessToken: 'x', refreshToken: 'y', expiresAt: '2030-01-01', refreshExpiresAt: '2030-01-10', userName: 'Ops', user: { id: 1, org_id: 5, email: 'ops@example.com', display_name: 'Ops', permissions: ['audit.view'] } }))
    vi.mocked(apiRequest).mockImplementation(async (path: string) => {
      if (path.startsWith('/food-beverage/metrics/summary?')) return { expected_breakfast_count: 12, actual_breakfast_count: 10, variance_count: -2, variance_percentage: Number.NaN }
      if (path.startsWith('/food-beverage/metrics/breakfast?')) return [{ date: '2026-05-01', value: 10 }]
      if (path.startsWith('/food-beverage/metrics/outlet-readiness?')) return [{ status: 'READY', value: 7 }]
      if (path.startsWith('/food-beverage/metrics/tasks?')) return [{ label: 'COMPLETED', value: 9 }]
      return []
    })
    renderWithProviders(<FBDashboardPage />, { route: '/food-beverage/dashboard' })
    expect(await screen.findByText('Expected breakfast count')).toBeInTheDocument()
    expect(screen.getAllByText('0').length).toBeGreaterThan(0)
    expect(screen.getByText('2026-05-01')).toBeInTheDocument()
    await userEvent.type(screen.getByLabelText('property_id'), '11')
    await waitFor(() => expect(vi.mocked(apiRequest).mock.calls.some((x) => String(x[0]).includes('property_id=11'))).toBe(true))
  })
})
