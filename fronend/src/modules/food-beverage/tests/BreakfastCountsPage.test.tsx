import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../../shared/api/client'
import { renderWithProviders } from '../../../test/utils'
import { BreakfastCountFormPage } from '../pages/BreakfastCountFormPage'
import { BreakfastCountsPage } from '../pages/BreakfastCountsPage'

vi.mock('../../../shared/api/client', () => ({ apiRequest: vi.fn() }))

describe('Breakfast count views', () => {
  it('renders list rows and validates form', async () => {
    localStorage.setItem('ticketing.auth', JSON.stringify({ accessToken: 'x', refreshToken: 'y', expiresAt: '2030-01-01', refreshExpiresAt: '2030-01-10', userName: 'Ops', user: { id: 1, org_id: 5, email: 'ops@example.com', display_name: 'Ops', permissions: ['audit.view'] } }))
    vi.mocked(apiRequest).mockImplementation(async (path: string, opts?: any) => {
      if (path.startsWith('/food-beverage/breakfast-counts?')) return { count: 1, results: [{ id: 1, service_date: '2026-05-01', property_id: 1, outlet_id: 2, expected_guest_count: 100, actual_guest_count: 90, in_house_guest_count: 95, complimentary_count: 20, paid_count: 70, no_show_count: 5, updated_at: '2026-05-01T10:00:00Z' }] }
      if (path === '/food-beverage/breakfast-counts' && opts?.method === 'POST') return { id: 1 }
      return { count: 0, results: [] }
    })
    renderWithProviders(<BreakfastCountsPage />, { route: '/food-beverage/breakfast-counts' })
    expect(await screen.findByText('2026-05-01')).toBeInTheDocument()

    renderWithProviders(<BreakfastCountFormPage />, { route: '/food-beverage/breakfast-counts/new' })
    await userEvent.type(screen.getByLabelText('Property'), '1')
    await userEvent.type(screen.getByLabelText('Outlet'), '2')
    await userEvent.type(screen.getByLabelText('Service Date'), '2026-05-01')
    await userEvent.clear(screen.getByLabelText('Actual Guests'))
    await userEvent.type(screen.getByLabelText('Actual Guests'), '-1')
    await userEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(await screen.findByText('All count fields must be non-negative.')).toBeInTheDocument()
  })
})
