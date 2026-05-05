import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { ApprovalTrail } from '../components/ApprovalTrail'
import { RiskComplianceAuditLogsPage } from '../pages/RiskComplianceAuditLogsPage'

vi.mock('../../../features/auth/authContext', () => ({ useAuth: () => ({ auth: { accessToken: 'x', user: { org_id: 1 } } }) }))
vi.mock('../hooks/useRiskCompliance', () => ({
  useRiskComplianceAuditLogs: () => ({ loading: false, error: '', data: { count: 1, results: [{ id: 1, actor_user_id: 2, action: 'risk_compliance_risk_created', target_type: 'risk', target_id: '99', metadata: { score: 9 }, created_at: '2026-01-01T00:00:00Z' }] } }),
}))

describe('Approval trails and audit logs', () => {
  it('renders timeline and permissioned approve/reject buttons', async () => {
    const user = userEvent.setup()
    const onApprove = vi.fn()
    const onReject = vi.fn()
    render(<ApprovalTrail entries={[{ approver: 'Manager', decision: 'PENDING', timestamp: '2026-01-01T00:00:00Z', comment: 'Waiting', status: 'PENDING' }]} canManage={true} onApprove={onApprove} onReject={onReject} />)
    await user.click(screen.getByRole('button', { name: 'Approve' }))
    await user.click(screen.getByRole('button', { name: 'Reject' }))
    expect(onApprove).toHaveBeenCalled()
    expect(onReject).toHaveBeenCalled()
  })

  it('renders audit events, supports pagination controls and metadata drawer', async () => {
    const user = userEvent.setup()
    render(<MemoryRouter><RiskComplianceAuditLogsPage /></MemoryRouter>)
    expect(screen.getByText('risk_compliance_risk_created')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Open' }))
    expect(screen.getByText(/"score": 9/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Next' })).toBeInTheDocument()
  })
})
