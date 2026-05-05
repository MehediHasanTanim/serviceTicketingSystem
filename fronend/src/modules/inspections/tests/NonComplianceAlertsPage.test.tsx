import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { NonComplianceAlertsPage } from '../pages/NonComplianceAlertsPage'

const ack = vi.fn(async () => ({}))
const res = vi.fn(async () => ({}))

vi.mock('../../../features/auth/authContext', () => ({ useAuth: () => ({ auth: { accessToken: 'x', user: { org_id: 1 } } }) }))
vi.mock('../hooks/useInspections', () => ({
  useNonComplianceAlerts: () => ({ loading: false, error: '', reload: vi.fn(), data: { count: 1, results: [{ id: 1, inspection_run_id: 2, checklist_item_id: 3, alert_type: 'ITEM_FAIL', severity: 'HIGH', message: 'm', assigned_to: 5, status: 'OPEN', created_at: '2026-01-01T00:00:00Z', resolved_at: null }] } }),
  useAcknowledgeNonComplianceAlert: () => ack,
  useResolveNonComplianceAlert: () => res,
}))

describe('NonComplianceAlertsPage', () => {
  it('renders rows and acknowledge action', async () => {
    const user = userEvent.setup()
    render(<MemoryRouter><NonComplianceAlertsPage /></MemoryRouter>)
    await user.click(screen.getByRole('button', { name: 'Acknowledge' }))
    expect(ack).toHaveBeenCalled()
    expect(screen.getByText('HIGH')).toBeInTheDocument()
  })
})
