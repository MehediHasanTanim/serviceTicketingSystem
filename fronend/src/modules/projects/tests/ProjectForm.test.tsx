import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ProjectForm } from '../components/ProjectForm'

describe('ProjectForm', () => {
  it('validates required, range and date rules', async () => {
    const onSubmit = vi.fn()
    render(<ProjectForm orgId={1} mode="create" onSubmit={onSubmit} />)
    await userEvent.click(screen.getByRole('button', { name: 'Create' }))
    expect(await screen.findByText('Title is required.')).toBeInTheDocument()

    await userEvent.type(screen.getByLabelText('Title'), 'Project A')
    await userEvent.type(screen.getByLabelText('Start date'), '2026-05-10')
    await userEvent.type(screen.getByLabelText('Planned end date'), '2026-05-01')
    await userEvent.clear(screen.getByLabelText('Progress %'))
    await userEvent.type(screen.getByLabelText('Progress %'), '101')
    await userEvent.click(screen.getByRole('button', { name: 'Create' }))
    expect(await screen.findByText('Planned end date must be after start date.')).toBeInTheDocument()
    expect(await screen.findByText('Progress must be 0-100.')).toBeInTheDocument()
  })
})
