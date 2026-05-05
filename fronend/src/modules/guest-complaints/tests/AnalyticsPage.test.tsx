import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { GuestComplaintAnalyticsPage } from '../pages/GuestComplaintAnalyticsPage'

vi.mock('../../../features/auth/authContext', () => ({ useAuth: () => ({ auth: { accessToken: 'x', user: { org_id: 1 } } }) }))
vi.mock('../hooks/useGuestComplaints', () => ({
  useGuestComplaintAnalytics: () => ({
    loading: false,
    error: '',
    reload: vi.fn(),
    data: {
      summary: { total_complaints: 0, open_complaints: 0, resolved_complaints: 0, escalated_complaints: 0, reopened_complaints: 0, sla_compliance_percentage: 0, complaints_by_category: [], complaints_by_severity: [] },
      trends: { results: [] },
      resolution: { average_resolution_time_hours: 0, resolved_count: 0 },
      satisfaction: { average_satisfaction_score: 0, low_satisfaction_count: 0, responses_count: 0 },
    },
  }),
}))

describe('GuestComplaintAnalyticsPage', () => {
  it('renders zero-safe KPI values', () => {
    render(<MemoryRouter><GuestComplaintAnalyticsPage /></MemoryRouter>)
    expect(screen.getByText('No trend rows.')).toBeInTheDocument()
    expect(screen.getByText('0.00%')).toBeInTheDocument()
  })
})
