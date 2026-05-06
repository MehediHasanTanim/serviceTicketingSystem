import { describe, expect, it, vi } from 'vitest'
import { screen } from '@testing-library/react'
import { IntegrationJobsPage } from '../pages/IntegrationJobsPage'
import { renderWithProviders } from '../../../test/utils'

vi.mock('../hooks/useIntegrations', () => ({
  useIntegrationJobs: () => ({ loading: false, error: '', data: { count: 1, results: [{ id: 9, correlation_id: 'corr-1', provider_code: 'PMS_A', job_type: 'occupancy_sync', direction: 'OUTBOUND', status: 'FAILED', source_entity_type: 'room', target_entity_type: 'pms_room', retry_count: 1, next_retry_at: '2026-01-01T00:00:00Z', started_at: '2026-01-01T00:00:00Z', completed_at: '2026-01-01T00:02:00Z' }] } }),
}))

describe('IntegrationJobsPage', () => {
  it('renders job rows and status badge', async () => {
    localStorage.setItem('ticketing.auth', JSON.stringify({ accessToken: 't', refreshToken: 'r', expiresAt: '', refreshExpiresAt: '', userName: 'u', user: { id: 1, org_id: 8, email: 'u@x.com', display_name: 'U' } }))
    renderWithProviders(<IntegrationJobsPage />, { route: '/integrations/jobs' })
    expect(await screen.findByText('corr-1')).toBeInTheDocument()
    expect(screen.getByText('FAILED')).toBeInTheDocument()
  })
})
