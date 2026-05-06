import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../../shared/api/client'
import { renderWithProviders } from '../../../test/utils'
import { OutletReadinessDetailPage } from '../pages/OutletReadinessDetailPage'

vi.mock('../../../shared/api/client', () => ({ apiRequest: vi.fn() }))
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<any>('react-router-dom')
  return { ...actual, useParams: () => ({ id: '7' }) }
})

describe('OutletReadinessDetailPage', () => {
  it('renders grouped checklist and validates fail comment and confirmation modal', async () => {
    localStorage.setItem('ticketing.auth', JSON.stringify({ accessToken: 'x', refreshToken: 'y', expiresAt: '2030-01-01', refreshExpiresAt: '2030-01-10', userName: 'Ops', user: { id: 1, org_id: 5, email: 'ops@example.com', display_name: 'Ops', permissions: ['audit.view'] } }))
    vi.mocked(apiRequest).mockImplementation(async (path: string) => {
      if (path.startsWith('/food-beverage/outlet-readiness/7?')) return { id: 7, readiness_date: '2026-05-01', property_id: 1, outlet_id: 2, shift: 'BREAKFAST', status: 'PENDING', checklist_score: 0, updated_at: '2026-05-01T10:00:00Z', checklist_items: [{ id: 11, name: 'Setup table', category: 'SERVICE_SETUP', is_required: true, result: 'PASS', comment: '' }] }
      return { id: 7 }
    })
    renderWithProviders(<OutletReadinessDetailPage />, { route: '/food-beverage/outlet-readiness/7' })
    expect(await screen.findByText('SERVICE_SETUP')).toBeInTheDocument()
    await userEvent.selectOptions(screen.getByLabelText('result-11'), 'FAIL')
    expect(await screen.findByText('FAIL item requires comment.')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Verify readiness' }))
    expect(await screen.findByRole('dialog', { name: 'Readiness confirmation' })).toBeInTheDocument()
  })
})
