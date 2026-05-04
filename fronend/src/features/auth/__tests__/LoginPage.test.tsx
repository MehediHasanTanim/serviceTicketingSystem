import { http, HttpResponse } from 'msw'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { LoginPage } from '../LoginPage'
import { server } from '../../../test/mocks/server'
import { renderWithProviders } from '../../../test/utils'

const navigateMock = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

describe('LoginPage', () => {
  beforeEach(() => {
    navigateMock.mockReset()
  })

  it('signs in successfully and redirects to home', async () => {
    server.use(
      http.post('*/auth/login', async () => {
        return HttpResponse.json({
          access: 'access-token',
          refresh: 'refresh-token',
          access_expires_at: '2030-01-01T00:00:00Z',
          refresh_expires_at: '2030-01-10T00:00:00Z',
        })
      }),
      http.get('*/me', async () => {
        return HttpResponse.json({
          id: 10,
          org_id: 1,
          email: 'admin@example.com',
          display_name: 'System Admin',
          permissions: ['users.view'],
        })
      }),
    )

    renderWithProviders(<LoginPage />, { route: '/login' })
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith('/home')
    })
  })

  it('renders API error message when login fails', async () => {
    server.use(
      http.post('*/auth/login', async () => {
        return HttpResponse.json({ detail: 'Invalid credentials' }, { status: 401 })
      }),
    )

    renderWithProviders(<LoginPage />, { route: '/login' })
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByText('Invalid credentials')).toBeInTheDocument()
    expect(navigateMock).not.toHaveBeenCalled()
  })

  it('submits trimmed email from the form', async () => {
    let submittedEmail = ''
    server.use(
      http.post('*/auth/login', async ({ request }) => {
        const body = (await request.json()) as { email?: string }
        submittedEmail = body.email || ''
        return HttpResponse.json({
          access: 'access-token',
          refresh: 'refresh-token',
          access_expires_at: '2030-01-01T00:00:00Z',
          refresh_expires_at: '2030-01-10T00:00:00Z',
        })
      }),
      http.get('*/me', async () => {
        return HttpResponse.json({
          id: 10,
          org_id: 1,
          email: 'admin@example.com',
          display_name: 'System Admin',
          permissions: ['users.view'],
        })
      }),
    )

    renderWithProviders(<LoginPage />, { route: '/login' })
    const emailInput = screen.getByRole('textbox', { name: /email/i })
    await userEvent.clear(emailInput)
    await userEvent.type(emailInput, '  admin@example.com  ')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith('/home')
    })
    expect(submittedEmail).toBe('admin@example.com')
  })
})
