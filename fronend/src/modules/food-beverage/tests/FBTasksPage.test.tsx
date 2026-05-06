import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../../shared/api/client'
import { renderWithProviders } from '../../../test/utils'
import { FBTasksPage } from '../pages/FBTasksPage'

vi.mock('../../../shared/api/client', () => ({ apiRequest: vi.fn() }))

describe('FBTasksPage', () => {
  it('renders tasks, opens assignment modal, and shows action confirmation', async () => {
    localStorage.setItem('ticketing.auth', JSON.stringify({ accessToken: 'x', refreshToken: 'y', expiresAt: '2030-01-01', refreshExpiresAt: '2030-01-10', userName: 'Ops', user: { id: 1, org_id: 5, email: 'ops@example.com', display_name: 'Ops', permissions: ['audit.view'] } }))
    vi.mocked(apiRequest).mockImplementation(async (path: string) => {
      if (path.startsWith('/food-beverage/tasks?')) return { count: 1, results: [{ id: 9, task_number: 'FB-9', outlet_id: 2, title: 'Prep buffet', task_type: 'BREAKFAST_PREP', priority: 'HIGH', status: 'IN_PROGRESS', assigned_to: 101, due_at: '2099-05-01T10:00:00Z', started_at: null, completed_at: null, updated_at: '2026-05-01T10:00:00Z' }] }
      return { id: 9 }
    })
    renderWithProviders(<FBTasksPage />, { route: '/food-beverage/tasks' })
    expect(await screen.findByText('FB-9')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Assign' }))
    expect(await screen.findByRole('dialog', { name: 'Assign task' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Complete' }))
    expect(await screen.findByRole('dialog', { name: 'Task action confirmation' })).toBeInTheDocument()
  })
})
