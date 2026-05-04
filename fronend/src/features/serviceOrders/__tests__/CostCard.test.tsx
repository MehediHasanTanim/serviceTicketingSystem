import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { CostCard } from '../components/CostCard'

describe('CostCard', () => {
  it('auto-calculates total and rejects negative input', async () => {
    const onSave = vi.fn()
    render(<CostCard partsCost="10" laborCost="20" compensationCost="5" onSave={onSave} />)

    expect(screen.getByText(/\$35\.00/)).toBeInTheDocument()
    await userEvent.clear(screen.getByLabelText('Parts cost'))
    await userEvent.type(screen.getByLabelText('Parts cost'), '-3')
    await userEvent.click(screen.getByRole('button', { name: 'Save Costs' }))
    expect(await screen.findByText('All values must be non-negative numbers.')).toBeInTheDocument()
    expect(onSave).not.toHaveBeenCalled()
  })
})
