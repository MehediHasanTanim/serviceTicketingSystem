import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { SnaggingForm, TechnicalAuditForm } from '../components/Forms'

describe('SnaggingForm', () => {
  it('requires title and submits payload', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    render(<SnaggingForm orgId={7} onSubmit={onSubmit} />)
    await userEvent.click(screen.getByRole('button', { name: 'Create Snagging Item' }))
    expect(await screen.findByText('Title is required.')).toBeInTheDocument()
  })
})

describe('TechnicalAuditForm', () => {
  it('validates score and findings for fail/partial', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    render(<TechnicalAuditForm orgId={7} onSubmit={onSubmit} />)
    await userEvent.type(screen.getByPlaceholderText('Title'), 'Electrical safety')
    await userEvent.type(screen.getByPlaceholderText('Auditor ID'), '4')
    await userEvent.type(screen.getByPlaceholderText('Score'), '200')
    await userEvent.click(screen.getByRole('button', { name: 'Create Technical Audit' }))
    expect(await screen.findByText('Score must be 0-100.')).toBeInTheDocument()
  })
})
