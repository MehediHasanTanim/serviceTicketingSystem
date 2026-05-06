import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ProjectBoard } from '../components/ProjectBoard'

const rows = [{ id: 1, org_id: 1, project_code: 'PRJ-1', title: 'Lobby', description: '', property_id: 1, department_id: 2, project_type: 'RENOVATION', priority: 'HIGH', status: 'IN_PROGRESS', owner_id: 3, manager_id: 4, start_date: '2026-01-01', planned_end_date: '2020-01-01', actual_end_date: null, budget_amount: '100', actual_cost: '10', progress_percentage: 35, created_by: 1, updated_by: 1, created_at: new Date().toISOString(), updated_at: new Date().toISOString() }] as any

describe('ProjectBoard', () => {
  it('renders table rows, badges, progress, overdue and supports row click', async () => {
    const onRowClick = vi.fn()
    render(<ProjectBoard view="table" projects={rows} loading={false} error="" onRetry={() => {}} onRowClick={onRowClick} />)
    expect(screen.getByText('PRJ-1')).toBeInTheDocument()
    expect(screen.getByText('HIGH')).toBeInTheDocument()
    expect(screen.getByText('IN_PROGRESS')).toBeInTheDocument()
    expect(screen.getByText('Overdue')).toBeInTheDocument()
    expect(screen.getByText('35%')).toBeInTheDocument()
    await userEvent.click(screen.getByText('PRJ-1'))
    expect(onRowClick).toHaveBeenCalledWith(1)
  })
})
