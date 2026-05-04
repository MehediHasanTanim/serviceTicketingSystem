import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { RoomStatusModal } from '../components/RoomStatusModal'

describe('RoomStatusModal', () => {
  it('requires reason for blocked or out-of-order updates and submits valid payload', async () => {
    const onSubmit = vi.fn()
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
    render(
      <RoomStatusModal
        open
        room={{ id: 1, room_id: 501, occupancy_status: 'VACANT', housekeeping_status: 'DIRTY', priority: 'MEDIUM', updated_at: new Date().toISOString(), updated_by: 1 }}
        onClose={() => {}}
        onSubmit={onSubmit}
      />,
    )

    await userEvent.selectOptions(screen.getByLabelText('Occupancy'), 'OUT_OF_ORDER')
    await userEvent.click(screen.getByRole('button', { name: 'Update' }))
    expect(await screen.findByText('Reason is required for blocked or out-of-order updates.')).toBeInTheDocument()

    await userEvent.type(screen.getByLabelText('Reason'), 'Maintenance work')
    await userEvent.click(screen.getByRole('button', { name: 'Update' }))

    expect(confirmSpy).toHaveBeenCalled()
    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ room_id: 501, occupancy_status: 'OUT_OF_ORDER', reason: 'Maintenance work' }))
    confirmSpy.mockRestore()
  })
})
