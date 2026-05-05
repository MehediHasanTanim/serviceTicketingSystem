import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { LifecycleActions } from '../components/LifecycleActions'

describe('LifecycleActions', () => {
  it('shows valid actions for status', () => {
    const onAction = vi.fn()
    render(<LifecycleActions status="RESOLVED" onAction={onAction} />)
    expect(screen.getByRole('button', { name: 'confirm' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'reopen' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'start' })).not.toBeInTheDocument()
  })

  it('requires reason for reopen/void/escalate', async () => {
    const onAction = vi.fn()
    render(<LifecycleActions status="RESOLVED" onAction={onAction} />)
    await userEvent.click(screen.getByRole('button', { name: 'reopen' }))
    await userEvent.click(screen.getByRole('button', { name: 'Confirm' }))
    expect(await screen.findByText('Reason is required.')).toBeInTheDocument()
  })
})
