import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { OrderForm } from '../components/OrderForm'

describe('OrderForm', () => {
  it('renders required fields and validation errors', async () => {
    const onSubmit = vi.fn()
    render(<OrderForm orgId={7} mode="create" users={[]} onSubmit={onSubmit} />)

    expect(screen.getByLabelText('Title')).toBeInTheDocument()
    expect(screen.getByLabelText('Customer')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Create' }))
    expect(await screen.findByText('Title is required.')).toBeInTheDocument()
    expect(await screen.findByText('Customer is required.')).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('submits correct payload and edit prefill works', async () => {
    const onSubmit = vi.fn()
    render(
      <OrderForm
        orgId={7}
        mode="edit"
        users={[{ id: 2, label: 'User #2' }]}
        initial={{
          id: 1, org_id: 7, ticket_number: 'SO-1', title: 'Old', description: 'Desc', customer_id: 33,
          asset_id: 9, created_by: 1, assigned_to: 2, priority: 'HIGH', type: 'REPAIR', status: 'ASSIGNED',
          due_date: '2026-05-10', scheduled_at: '2026-05-03T09:00:00Z', completed_at: null,
          estimated_cost: '0.00', parts_cost: '0.00', labor_cost: '0.00', compensation_cost: '0.00', total_cost: '0.00',
          version: 1, created_at: '2026-05-01T00:00:00Z', updated_at: '2026-05-01T00:00:00Z',
        }}
        onSubmit={onSubmit}
      />,
    )

    expect((screen.getByLabelText('Title') as HTMLInputElement).value).toBe('Old')
    await userEvent.clear(screen.getByLabelText('Title'))
    await userEvent.type(screen.getByLabelText('Title'), 'Updated')
    await userEvent.click(screen.getByRole('button', { name: 'Update' }))

    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ org_id: 7, title: 'Updated', customer_id: 33 }))
  })
})
