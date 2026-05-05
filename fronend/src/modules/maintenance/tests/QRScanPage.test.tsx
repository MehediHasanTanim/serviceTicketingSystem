import { fireEvent, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { QRScanPage } from '../pages/QRScanPage'
import { renderWithProviders } from '../../../test/utils'

const lookupAssetByQR = vi.fn()
const createTaskFromQR = vi.fn()
vi.mock('../api/maintenance.api', () => ({
  lookupAssetByQR: (...args: any[]) => lookupAssetByQR(...args),
  createTaskFromQR: (...args: any[]) => createTaskFromQR(...args),
}))

function setup() {
  localStorage.setItem('ticketing.auth', JSON.stringify({ accessToken: 'token', refreshToken: 'r', expiresAt: '', refreshExpiresAt: '', userName: 'x', user: { id: 1, org_id: 1, email: 'a@a.com', display_name: 'A' } }))
  return renderWithProviders(<QRScanPage />)
}

describe('QR flow', () => {
  it('manual QR input triggers lookup and shows not found', async () => {
    lookupAssetByQR.mockRejectedValueOnce(new Error('Asset not found'))
    setup()
    fireEvent.change(screen.getByPlaceholderText('Enter QR code'), { target: { value: 'NOPE' } })
    fireEvent.click(screen.getByText('Lookup'))
    await waitFor(() => expect(screen.getByText(/not found/i)).toBeInTheDocument())
  })

  it('renders found asset summary', async () => {
    lookupAssetByQR.mockResolvedValueOnce({ asset: { id: 7, name: 'Generator', asset_code: 'AST-1' }, current_status: 'ACTIVE', open_maintenance_tasks: [], recent_logbook_entries: [] })
    setup()
    fireEvent.change(screen.getByPlaceholderText('Enter QR code'), { target: { value: 'QR-1' } })
    fireEvent.click(screen.getByText('Lookup'))
    await waitFor(() => expect(screen.getByText('Generator')).toBeInTheDocument())
  })
})
