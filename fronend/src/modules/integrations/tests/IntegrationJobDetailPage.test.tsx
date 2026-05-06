import { describe, expect, it, vi } from 'vitest'
import { Route, Routes } from 'react-router-dom'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { IntegrationJobDetailPage } from '../pages/IntegrationJobDetailPage'
import { renderWithProviders } from '../../../test/utils'

const retry = vi.fn(async () => ({}))
const dead = vi.fn(async () => ({}))
vi.mock('../hooks/useIntegrations', () => ({
  useIntegrationJobDetail: () => ({ loading: false, error: '', reload: vi.fn(), data: { id: 7, correlation_id: 'corr-7', status: 'FAILED', error_code: 'E500', error_message: 'Oops', request_payload: { token: 'abc', foo: 1 }, response_payload: { password: '123', ok: false }, attempts: [{ at: '2026-01-01T00:00:00Z', status: 'FAILED', error_message: 'x' }] } }),
  useRetryIntegrationJob: () => retry,
  useMoveIntegrationJobToDeadLetter: () => dead,
}))

describe('IntegrationJobDetailPage', () => {
  it('masks sensitive payload fields and supports actions', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    localStorage.setItem('ticketing.auth', JSON.stringify({ accessToken: 't', refreshToken: 'r', expiresAt: '', refreshExpiresAt: '', userName: 'u', user: { id: 1, org_id: 8, email: 'u@x.com', display_name: 'U' } }))
    renderWithProviders(<Routes><Route path='/integrations/jobs/:id' element={<IntegrationJobDetailPage />} /></Routes>, { route: '/integrations/jobs/7' })
    expect(await screen.findByText('corr-7')).toBeInTheDocument()
    expect(screen.getAllByText((_, el) => (el?.textContent || '').includes('***MASKED***')).length).toBeGreaterThan(1)
    await userEvent.click(screen.getByRole('button', { name: 'Retry job' }))
    await userEvent.click(screen.getByRole('button', { name: 'Move to dead letter' }))
    expect(retry).toHaveBeenCalled()
    expect(dead).toHaveBeenCalled()
  })
})
