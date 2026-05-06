import { describe, expect, it, vi } from 'vitest'
import { Route, Routes } from 'react-router-dom'
import { screen } from '@testing-library/react'
import { IntegrationProviderFormPage } from '../pages/IntegrationProviderFormPage'
import { renderWithProviders } from '../../../test/utils'

vi.mock('../hooks/useIntegrations', () => ({
  useCreateIntegrationProvider: () => vi.fn(),
  useUpdateIntegrationProvider: () => vi.fn(),
  useIntegrationProviderDetail: () => ({ data: { provider_code: 'PMS_X', name: 'PMS X', provider_type: 'PMS', status: 'ACTIVE', base_url: 'https://pms.test', auth_type: 'API_KEY', credentials_secret_ref: 'vault/pms', timeout_seconds: 15, retry_policy: { max_retries: 2 }, config: { foo: 'bar' } } }),
}))

describe('IntegrationProviderFormPage', () => {
  it('prefills safe values in edit mode and masks secret ref', async () => {
    localStorage.setItem('ticketing.auth', JSON.stringify({ accessToken: 't', refreshToken: 'r', expiresAt: '', refreshExpiresAt: '', userName: 'u', user: { id: 1, org_id: 8, email: 'u@x.com', display_name: 'U' } }))
    renderWithProviders(<Routes><Route path='/integrations/providers/:id/edit' element={<IntegrationProviderFormPage />} /></Routes>, { route: '/integrations/providers/11/edit' })
    expect(await screen.findByDisplayValue('PMS_X')).toBeInTheDocument()
    expect(screen.getByLabelText('Credentials Secret Ref')).toHaveValue('***masked***')
  })
})
