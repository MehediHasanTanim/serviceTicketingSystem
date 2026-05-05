import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { GuestComplaintAlertsPage } from '../pages/GuestComplaintAlertsPage'

vi.mock('../../../features/auth/authContext', () => ({ useAuth: () => ({ auth: { accessToken: 'x', user: { org_id: 1 } } }) }))
vi.mock('../hooks/useGuestComplaints', () => ({
  useComplaintAlerts: () => ({
    loading: false,
    error: '',
    reload: vi.fn(),
    data: [
      {
        reason: 'CRITICAL',
        triggered_at: '2026-01-01T00:00:00Z',
        complaint: { id: 1, complaint_number: 'GC-1', severity: 'CRITICAL', status: 'ESCALATED', guest_name: 'Jane', room_id: 501, assigned_to: 9, due_at: null },
      },
    ],
  }),
}))

describe('GuestComplaintAlertsPage', () => {
  it('renders alert items', () => {
    render(<MemoryRouter><GuestComplaintAlertsPage /></MemoryRouter>)
    expect(screen.getByText('GC-1')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Open' })).toBeInTheDocument()
  })
})
