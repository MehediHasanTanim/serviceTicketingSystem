import { fireEvent, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { PMCalendarPage } from '../pages/PMCalendarPage'
import { renderWithProviders } from '../../../test/utils'

vi.mock('../hooks/useMaintenance', () => ({
  usePMCalendar: () => ({ loading: false, calendarItems: [{ id: 1, title: 'PM-1', at: new Date().toISOString(), priority: 'HIGH', status: 'OPEN', overdue: true }] }),
}))

function setup() {
  localStorage.setItem('ticketing.auth', JSON.stringify({ accessToken: 'token', refreshToken: 'r', expiresAt: '', refreshExpiresAt: '', userName: 'x', user: { id: 1, org_id: 1, email: 'a@a.com', display_name: 'A' } }))
  return renderWithProviders(<PMCalendarPage />)
}

describe('PMCalendarPage', () => {
  it('renders scheduled items and overdue indicator', () => {
    setup()
    expect(screen.getByText(/PM-1/)).toBeInTheDocument()
    expect(screen.getByText(/Overdue/)).toBeInTheDocument()
  })

  it('date navigation updates header', () => {
    setup()
    const before = screen.getByText(/\w+ \d{4}/).textContent
    fireEvent.click(screen.getByText('Next'))
    const after = screen.getByText(/\w+ \d{4}/).textContent
    expect(after).not.toBe(before)
  })
})
