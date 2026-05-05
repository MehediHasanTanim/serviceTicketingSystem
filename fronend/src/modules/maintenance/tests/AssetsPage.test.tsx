import { fireEvent, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { AssetsPage } from '../pages/AssetsPage'
import { renderWithProviders } from '../../../test/utils'

const createAsset = vi.fn()
vi.mock('../api/maintenance.api', () => ({ createAsset: (...args: any[]) => createAsset(...args) }))
vi.mock('../hooks/useMaintenance', () => ({ useAssets: () => ({ data: { results: [], count: 0, page: 1, page_size: 10 }, loading: false, error: '', reload: vi.fn() }) }))

function setup() {
  localStorage.setItem('ticketing.auth', JSON.stringify({ accessToken: 'token', refreshToken: 'r', expiresAt: '', refreshExpiresAt: '', userName: 'x', user: { id: 1, org_id: 1, email: 'a@a.com', display_name: 'A' } }))
  return renderWithProviders(<AssetsPage />)
}

describe('AssetsPage', () => {
  it('rejects invalid warranty date range', async () => {
    const { container } = setup()
    fireEvent.click(screen.getByText('New Asset'))
    const dates = container.querySelectorAll('input[type="date"]')
    fireEvent.change(dates[0] as HTMLInputElement, { target: { value: '2026-05-10' } })
    fireEvent.change(dates[1] as HTMLInputElement, { target: { value: '2026-05-01' } })
    fireEvent.click(screen.getByText('Save'))
    expect(await screen.findByText(/Warranty expiry must be after purchase date/)).toBeInTheDocument()
  })

  it('shows API unique code error', async () => {
    createAsset.mockRejectedValueOnce(new Error('Asset code already exists'))
    setup()
    fireEvent.click(screen.getByText('New Asset'))
    fireEvent.change(screen.getByPlaceholderText('Asset Code'), { target: { value: 'A-1' } })
    fireEvent.change(screen.getByPlaceholderText('Name'), { target: { value: 'Asset' } })
    fireEvent.click(screen.getByText('Save'))
    await waitFor(() => expect(screen.getByText(/already exists/)).toBeInTheDocument())
  })
})
