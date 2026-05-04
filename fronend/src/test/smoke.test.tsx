import { describe, expect, it } from 'vitest'
import { screen } from '@testing-library/react'
import { LoginPage } from '../features/auth/LoginPage'
import { renderWithProviders } from './utils'

describe('frontend test setup', () => {
  it('renders the login screen', () => {
    renderWithProviders(<LoginPage />, { route: '/login' })
    expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
  })
})
