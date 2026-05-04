import { render, type RenderOptions } from '@testing-library/react'
import { type ReactElement, type ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '../features/auth/authContext'

type WrapperProps = {
  children: ReactNode
}

type ExtendedRenderOptions = Omit<RenderOptions, 'wrapper'> & {
  route?: string
}

export function renderWithProviders(ui: ReactElement, options: ExtendedRenderOptions = {}) {
  const { route = '/', ...renderOptions } = options

  function Wrapper({ children }: WrapperProps) {
    return (
      <MemoryRouter
        initialEntries={[route]}
        future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
      >
        <AuthProvider>{children}</AuthProvider>
      </MemoryRouter>
    )
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions })
}
