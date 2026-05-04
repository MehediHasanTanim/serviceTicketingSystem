import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { TaskBoard } from '../components/TaskBoard'

describe('TaskBoard', () => {
  it('renders tasks grouped by status and overdue indicator', () => {
    render(<TaskBoard loading={false} error="" onRetry={() => {}} tasks={[
      { id: '1', roomNumber: '101', taskType: 'CLEANING', priority: 'HIGH', status: 'PENDING', overdue: true, source: 'audit' },
      { id: '2', roomNumber: '102', taskType: 'INSPECTION', priority: 'LOW', status: 'COMPLETED', overdue: false, source: 'audit' },
    ]} />)

    expect(screen.getByText('PENDING (1)')).toBeInTheDocument()
    expect(screen.getByText('COMPLETED (1)')).toBeInTheDocument()
    expect(screen.getByText('Overdue')).toBeInTheDocument()
  })

  it('shows loading and empty states', () => {
    const { rerender } = render(<TaskBoard loading error="" onRetry={() => {}} tasks={[]} />)
    expect(screen.getByText('Loading housekeeping tasks...')).toBeInTheDocument()
    rerender(<TaskBoard loading={false} error="" onRetry={() => {}} tasks={[]} />)
    expect(screen.getByText('No housekeeping tasks found.')).toBeInTheDocument()
  })
})
