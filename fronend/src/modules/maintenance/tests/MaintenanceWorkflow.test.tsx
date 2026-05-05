import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MaintenanceOrderForm } from '../components/MaintenanceOrderForm'
import { getAllowedActions } from '../components/utils'

describe('Maintenance workflow components', () => {
  it('validates required title', async () => {
    const onSubmit = vi.fn()
    render(<MaintenanceOrderForm orgId={1} mode="create" onSubmit={onSubmit} />)
    fireEvent.click(screen.getByText('Create Task'))
    expect(await screen.findByText('Title is required.')).toBeInTheDocument()
  })

  it('shows valid status action buttons by status', () => {
    expect(getAllowedActions('OPEN')).toContain('start')
    expect(getAllowedActions('IN_PROGRESS')).toContain('complete')
    expect(getAllowedActions('COMPLETED')).toHaveLength(0)
  })
})
