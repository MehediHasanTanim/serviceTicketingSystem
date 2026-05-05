import { fireEvent, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MaintenanceAuditLogsPage } from '../pages/MaintenanceAuditLogsPage'
import { renderWithProviders } from '../../../test/utils'

vi.mock('../hooks/useMaintenance', () => ({
  useMaintenanceAuditLogs: () => ({
    loading: false,
    error: '',
    data: {
      count: 1,
      page: 1,
      page_size: 10,
      results: [{ id: 1, actor_user_id: 2, action: 'maintenance_task_created', target_type: 'maintenance_task', target_id: '5', metadata: { key: 'value' }, created_at: new Date().toISOString() }],
    },
  }),
}))

function setup() {
  localStorage.setItem('ticketing.auth', JSON.stringify({ accessToken: 'token', refreshToken: 'r', expiresAt: '', refreshExpiresAt: '', userName: 'x', user: { id: 1, org_id: 1, email: 'a@a.com', display_name: 'A' } }))
  return renderWithProviders(<MaintenanceAuditLogsPage />)
}

describe('Maintenance audit logs', () => {
  it('renders audit events and opens metadata drawer', () => {
    setup()
    expect(screen.getByText('maintenance_task_created')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Open'))
    expect(screen.getByText('Metadata')).toBeInTheDocument()
  })
})
