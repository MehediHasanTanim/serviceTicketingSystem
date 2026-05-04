import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { StatusTransitionControls } from '../components/StatusTransitionControls'

describe('StatusTransitionControls', () => {
  it('shows valid buttons by status and hides invalid actions', () => {
    const onAction = vi.fn()
    render(<StatusTransitionControls status="OPEN" onAction={onAction} />)
    expect(screen.getByRole('button', { name: 'Assign' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Void' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Complete' })).not.toBeInTheDocument()
  })

  it('requires reason for defer/void and confirms action', async () => {
    const onAction = vi.fn()
    render(<StatusTransitionControls status="ASSIGNED" onAction={onAction} />)

    await userEvent.click(screen.getByRole('button', { name: 'Defer' }))
    await userEvent.click(screen.getByRole('button', { name: 'Confirm' }))
    expect(await screen.findByText('Reason is required.')).toBeInTheDocument()
    await userEvent.type(screen.getByLabelText('Reason'), 'Waiting parts')
    await userEvent.click(screen.getByRole('button', { name: 'Confirm' }))

    expect(onAction).toHaveBeenCalledWith('defer', 'Waiting parts')
  })
})
