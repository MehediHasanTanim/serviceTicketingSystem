import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'

vi.mock('../features/home/HomePage', () => ({
  HomePage: () => <div>Home Mock</div>,
}))

vi.mock('../features/auth/LoginPage', () => ({
  LoginPage: () => <div>Login Mock</div>,
}))

vi.mock('../features/auth/ActivatePage', () => ({
  ActivatePage: () => <div>Activate Mock</div>,
}))

vi.mock('../features/auth/ActivateSuccessPage', () => ({
  ActivateSuccessPage: () => <div>Activate Success Mock</div>,
}))

describe('App protected route', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('redirects unauthenticated /home requests to login', async () => {
    window.history.pushState({}, '', '/home')

    render(<App />)

    expect(await screen.findByText('Login Mock')).toBeInTheDocument()
    expect(screen.queryByText('Home Mock')).not.toBeInTheDocument()
  })

  it('allows /home when access token is present', async () => {
    localStorage.setItem(
      'ticketing.auth',
      JSON.stringify({
        accessToken: 'access-token',
        refreshToken: 'refresh-token',
        expiresAt: '2030-01-01T00:00:00Z',
        refreshExpiresAt: '2030-01-10T00:00:00Z',
        userName: 'Test User',
        user: { id: 1, org_id: 1, email: 'test@example.com', display_name: 'Test User' },
      }),
    )
    window.history.pushState({}, '', '/home')

    render(<App />)

    expect(await screen.findByText('Home Mock')).toBeInTheDocument()
    expect(screen.queryByText('Login Mock')).not.toBeInTheDocument()
  })
})
