import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { ProjectTimeline } from '../components/ProjectTimeline'
import { AuditLogs } from '../components/AuditLogs'

describe('ProjectTimeline', () => {
  it('renders timeline events', () => {
    render(<ProjectTimeline loading={false} error="" events={[{ id: 1, project_id: 1, event_type: 'project_created', previous_status: null, new_status: 'DRAFT', progress_percentage: 0, message: 'Created', metadata: {}, actor_id: 10, created_at: '2026-05-01T00:00:00Z' }]} />)
    expect(screen.getByText('project_created')).toBeInTheDocument()
    expect(screen.getByText(/Progress: 0%/)).toBeInTheDocument()
  })
})

describe('AuditLogs', () => {
  it('opens metadata drawer', async () => {
    render(<AuditLogs rows={[{ id: 1, org_id: 1, property_id: null, actor_user_id: 2, action: 'project_updated', target_type: 'project', target_id: '1', metadata: { field: 'status' }, ip_address: '', user_agent: '', created_at: '2026-05-01T00:00:00Z' }]} />)
    await userEvent.click(screen.getByRole('button', { name: 'Open' }))
    expect(screen.getByText('Metadata')).toBeInTheDocument()
  })
})
