import { screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { renderWithProviders } from '../../../test/utils'
import { HousekeepingKpiPage } from '../pages/HousekeepingKpiPage'

vi.mock('../hooks/useHousekeepingKpis', () => ({
  useHousekeepingKpis: vi.fn(() => ({
    summary: {
      total_tasks_created: 0,
      total_tasks_completed: 0,
      pending_tasks_count: 0,
      overdue_tasks_count: 0,
      avg_completion_minutes: 0,
      avg_room_turnaround_minutes: 0,
      sla_compliance_pct: 0,
    },
    staff: [{ staff_id: 9, display_name: 'Alex', tasks_completed: 4, avg_completion_minutes: 22 }],
    turnaround: { events: 1, average_minutes: 25 },
    loading: false,
    error: '',
    reload: vi.fn(),
  })),
}))

describe('HousekeepingKpiPage', () => {
  it('renders zero-safe KPI cards and staff rows', async () => {
    localStorage.setItem('ticketing.auth', JSON.stringify({ accessToken: 'x', refreshToken: 'y', expiresAt: '2030-01-01', refreshExpiresAt: '2030-01-10', userName: 'Ops', user: { id: 1, org_id: 3, email: 'ops@example.com', display_name: 'Ops', permissions: ['housekeeping.view'] } }))
    renderWithProviders(<HousekeepingKpiPage />, { route: '/housekeeping/kpi' })
    expect(await screen.findByText('Total Created')).toBeInTheDocument()
    expect(screen.getAllByText('0').length).toBeGreaterThan(3)
    expect(screen.getByText('Alex')).toBeInTheDocument()
  })
})
