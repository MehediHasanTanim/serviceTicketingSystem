import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { AuthProvider, useAuth } from '../authContext'
import { apiRequest } from '../../../shared/api/client'

vi.mock('../../../shared/api/client', () => ({
  apiRequest: vi.fn(),
}))

function AuthHarness() {
  const { auth, login, logout } = useAuth()
  return (
    <div>
      <button
        onClick={() =>
          login({
            org_id: 7,
            email: 'admin@example.com',
            password: 'StrongPass1!',
          })
        }
      >
        Trigger Login
      </button>
      <button onClick={() => logout()}>Trigger Logout</button>
      <div data-testid="auth-user-name">{auth?.userName || ''}</div>
    </div>
  )
}

describe('authContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('maps login response tokens/user and stores auth payload', async () => {
    const apiMock = vi.mocked(apiRequest)
    apiMock.mockImplementation(async (path) => {
      if (path === '/auth/login') {
        return {
          access: 'access-token',
          refresh: 'refresh-token',
          access_expires_at: '2030-01-01T00:00:00Z',
          refresh_expires_at: '2030-01-10T00:00:00Z',
        }
      }
      if (path === '/me') {
        return {
          id: 1,
          org_id: 7,
          email: 'admin@example.com',
          display_name: 'System Admin',
          permissions: ['users.manage'],
        }
      }
      return null
    })

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>
    )

    await userEvent.click(screen.getByRole('button', { name: 'Trigger Login' }))

    await waitFor(() => {
      expect(screen.getByTestId('auth-user-name')).toHaveTextContent('System Admin')
    })

    expect(apiMock).toHaveBeenNthCalledWith(
      1,
      '/auth/login',
      expect.objectContaining({ method: 'POST' }),
    )
    expect(apiMock).toHaveBeenNthCalledWith(
      2,
      '/me',
      expect.objectContaining({
        method: 'GET',
        headers: { Authorization: 'Bearer access-token' },
      }),
    )

    const stored = JSON.parse(localStorage.getItem('ticketing.auth') || '{}')
    expect(stored).toMatchObject({
      accessToken: 'access-token',
      refreshToken: 'refresh-token',
      expiresAt: '2030-01-01T00:00:00Z',
      refreshExpiresAt: '2030-01-10T00:00:00Z',
      userName: 'System Admin',
    })
  })

  it('calls logout endpoint with bearer token and clears persisted auth', async () => {
    localStorage.setItem(
      'ticketing.auth',
      JSON.stringify({
        accessToken: 'persisted-access',
        refreshToken: 'persisted-refresh',
        expiresAt: '2030-01-01T00:00:00Z',
        refreshExpiresAt: '2030-01-10T00:00:00Z',
        userName: 'Persisted User',
        user: { id: 9, org_id: 1, email: 'persisted@example.com', display_name: 'Persisted User' },
      }),
    )
    const apiMock = vi.mocked(apiRequest)
    apiMock.mockResolvedValue(null)

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>
    )

    expect(screen.getByTestId('auth-user-name')).toHaveTextContent('Persisted User')
    await userEvent.click(screen.getByRole('button', { name: 'Trigger Logout' }))

    await waitFor(() => {
      expect(screen.getByTestId('auth-user-name')).toHaveTextContent('')
    })
    expect(apiMock).toHaveBeenCalledWith(
      '/auth/logout',
      expect.objectContaining({
        method: 'POST',
        headers: { Authorization: 'Bearer persisted-access' },
      }),
    )
    expect(localStorage.getItem('ticketing.auth')).toBeNull()
  })
})
