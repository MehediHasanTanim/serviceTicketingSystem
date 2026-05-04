import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { AssignmentModal } from '../components/AssignmentModal'

describe('AssignmentModal', () => {
  it('opens, filters users, prevents same assignee, and submits mutation', async () => {
    const onSubmit = vi.fn()
    render(
      <AssignmentModal
        open
        users={[{ id: 1, label: 'Alice' }, { id: 2, label: 'Bob' }]}
        currentAssigneeId={1}
        onClose={() => {}}
        onSubmit={onSubmit}
        reassign
      />,
    )

    expect(screen.getByRole('dialog', { name: 'Reassign order' })).toBeInTheDocument()
    await userEvent.type(screen.getByLabelText('Search users'), 'Ali')
    await userEvent.selectOptions(screen.getByLabelText('Assignee'), '1')
    await userEvent.click(screen.getByRole('button', { name: 'Submit' }))
    expect(await screen.findByText('Please select a different assignee.')).toBeInTheDocument()

    await userEvent.clear(screen.getByLabelText('Search users'))
    await userEvent.selectOptions(screen.getByLabelText('Assignee'), '2')
    await userEvent.click(screen.getByRole('button', { name: 'Submit' }))
    expect(await screen.findByText('Reason is required for reassignment.')).toBeInTheDocument()
    await userEvent.type(screen.getByLabelText(/Reason/), 'Workload rebalance')
    await userEvent.click(screen.getByRole('button', { name: 'Submit' }))
    expect(onSubmit).toHaveBeenCalledWith(2, 'Workload rebalance')
  })
})
