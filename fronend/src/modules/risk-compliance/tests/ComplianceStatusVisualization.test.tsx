import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { ComplianceCheckDetailPage } from '../pages/ComplianceCheckDetailPage'
import { ComplianceStatusBadge, EvidenceRequiredMarker, OverdueIndicator } from '../components/ComplianceStatusBadge'

vi.mock('../../../features/auth/authContext', () => ({ useAuth: () => ({ auth: { accessToken: 'x', user: { org_id: 1 } } }) }))
vi.mock('../hooks/useRiskCompliance', () => ({
  useComplianceCheckDetail: () => ({ data: { id: 9, requirement_id: 2, due_at: '2020-01-01T00:00:00Z', status: 'PENDING', updated_at: '2026-01-01T00:00:00Z' }, loading: false, error: '', reload: vi.fn() }),
  useComplianceRequirementDetail: () => ({ data: { checklist_items: [{ title: 'Attach evidence', description: '', evidence_required: true }] } }),
  useApprovalTrail: () => ({ data: { count: 0, results: [] }, reload: vi.fn() }),
  useDecideApprovalTrail: () => vi.fn(),
  useSubmitComplianceCheck: () => vi.fn(),
  useWaiveComplianceCheck: () => vi.fn(),
}))

describe('Compliance status visualization', () => {
  it('renders status badge, overdue indicator and evidence-required marker', () => {
    render(<><ComplianceStatusBadge status="NON_COMPLIANT" /><OverdueIndicator dueAt="2020-01-01T00:00:00Z" status="PENDING" /><EvidenceRequiredMarker required={true} /></>)
    expect(screen.getByText('NON_COMPLIANT')).toBeInTheDocument()
    expect(screen.getByText('Overdue')).toBeInTheDocument()
    expect(screen.getByText('Evidence Required')).toBeInTheDocument()
  })

  it('shows waiver confirmation modal and non-compliant reason requirement', async () => {
    const user = userEvent.setup()
    render(<MemoryRouter initialEntries={['/risk-compliance/checks/9']}><ComplianceCheckDetailPage /></MemoryRouter>)
    await user.click(screen.getByLabelText(/Mark as compliant/i))
    await user.click(screen.getByRole('button', { name: 'Submit' }))
    expect(screen.getByRole('dialog', { name: 'Submit confirmation' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Confirm' }))
    expect(screen.getByText(/Reason is required for non-compliant submission/i)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Waive' }))
    expect(screen.getByRole('dialog', { name: 'Waive confirmation' })).toBeInTheDocument()
  })
})
