import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ComplaintForm } from '../components/ComplaintForm'

describe('ComplaintForm', () => {
  it('shows required validation errors', async () => {
    const onSubmit = vi.fn()
    render(<ComplaintForm orgId={1} mode="create" onSubmit={onSubmit} />)
    await userEvent.click(screen.getByRole('button', { name: 'Create' }))
    expect(await screen.findByText('Guest name is required.')).toBeInTheDocument()
    expect(await screen.findByText('Property is required.')).toBeInTheDocument()
    expect(await screen.findByText('Title is required.')).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('submits payload and disables on saving', async () => {
    const onSubmit = vi.fn()
    render(<ComplaintForm orgId={8} mode="create" saving onSubmit={onSubmit} />)
    expect(screen.getByRole('button', { name: 'Saving...' })).toBeDisabled()
  })
})
