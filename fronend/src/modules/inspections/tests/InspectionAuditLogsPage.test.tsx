import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { InspectionAuditLogsPage } from '../pages/InspectionAuditLogsPage'

vi.mock('../../../features/auth/authContext', () => ({ useAuth: () => ({ auth: { accessToken: 'x', user: { org_id: 1 } } }) }))
vi.mock('../hooks/useInspections', () => ({
  useInspectionAuditLogs: () => ({ loading: false, error: '', data: { count: 1, results: [{ id: 1, actor_user_id: 2, action: 'inspection_run_completed', target_type: 'inspection_run', target_id: '9', metadata: { score: 95 }, created_at: '2026-01-01T00:00:00Z' }] } }),
}))

describe('InspectionAuditLogsPage', () => {
  it('renders audit logs and opens metadata drawer', async () => {
    const user = userEvent.setup()
    render(<MemoryRouter><InspectionAuditLogsPage /></MemoryRouter>)
    expect(screen.getByText('inspection_run_completed')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Open' }))
    expect(screen.getByText(/\"score\": 95/)).toBeInTheDocument()
  })
})
