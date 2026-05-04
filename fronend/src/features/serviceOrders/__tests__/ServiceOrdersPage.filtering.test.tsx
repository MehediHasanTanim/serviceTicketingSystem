import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ServiceOrdersPage } from '../ServiceOrdersPage'
import { renderWithProviders } from '../../../test/utils'
import { apiRequest } from '../../../shared/api/client'

vi.mock('../../../shared/api/client', () => ({ apiRequest: vi.fn() }))

function setAuth() {
  localStorage.setItem('ticketing.auth', JSON.stringify({
    accessToken: 'token', refreshToken: 'r', expiresAt: '', refreshExpiresAt: '', userName: 'Ops',
    user: { id: 1, org_id: 3, email: 'ops@test.com', display_name: 'Ops', permissions: ['service_orders.view', 'service_orders.manage'] },
  }))
}

describe('ServiceOrdersPage list filtering', () => {
  it('filters, paginates, and debounces search API params', async () => {
    setAuth()
    vi.mocked(apiRequest).mockResolvedValue({
      results: [{
        id: 12, org_id: 3, ticket_number: 'SO-22', title: 'Test', description: '', customer_id: 77, asset_id: null, created_by: 1,
        assigned_to: null, priority: 'MEDIUM', type: 'OTHER', status: 'OPEN', due_date: null, scheduled_at: null, completed_at: null,
        estimated_cost: '0.00', parts_cost: '0.00', labor_cost: '0.00', compensation_cost: '0.00', total_cost: '0.00',
        version: 1, created_at: '2026-05-01T00:00:00Z', updated_at: '2026-05-02T00:00:00Z',
      }],
      count: 25, page: 1, page_size: 10,
    })
    renderWithProviders(<ServiceOrdersPage />, { route: '/service-orders' })

    await userEvent.type(screen.getByPlaceholderText('Search by title or ticket'), 'SO-22')
    await new Promise((resolve) => setTimeout(resolve, 360))

    await userEvent.click(screen.getByRole('button', { name: 'Next' }))
    await userEvent.type(screen.getByPlaceholderText('Customer ID'), '77')
    await userEvent.click(screen.getByRole('button', { name: /Title/ }))

    await waitFor(() => {
      const calls = vi.mocked(apiRequest).mock.calls.filter(([p]) => String(p).startsWith('/service-orders?'))
      expect(calls.length).toBeGreaterThan(0)
      const sawPageTwo = calls.some(([path]) => new URL(`http://localhost${String(path)}`).searchParams.get('page') === '2')
      expect(sawPageTwo).toBe(true)
      const [last] = calls[calls.length - 1] as [string]
      const params = new URL(`http://localhost${last}`).searchParams
      expect(params.get('q')).toBe('SO-22')
      expect(params.get('page')).toBe('1')
      expect(params.get('customer_id')).toBe('77')
      expect(params.get('sort_by')).toBe('title')
    })
  }, 10000)
})
