import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { LegalRecordDetailPage } from '../pages/LegalRecordDetailPage'
import { AuditRecordDetailPage } from '../pages/AuditRecordDetailPage'

vi.mock('../../../features/auth/authContext', () => ({ useAuth: () => ({ auth: { accessToken: 'x', user: { org_id: 1 } } }) }))
vi.mock('../hooks/useRiskCompliance', () => ({
  useLegalRecordDetail: () => ({ data: { record_code: 'L-1', status: 'ACTIVE', expiry_date: '2026-12-31', renewal_due_at: '2026-11-01T00:00:00Z' } }),
  useCreateLegalRecord: () => vi.fn(),
  useUpdateLegalRecord: () => vi.fn(),
  useApprovalTrail: () => ({ data: { count: 0, results: [] }, reload: vi.fn() }),
  useDecideApprovalTrail: () => vi.fn(),
  useAuditRecordDetail: () => ({ data: { id: 2, audit_code: 'A-1', result: 'FAIL', score: '72', findings_summary: 'Missing controls', corrective_actions_required: true } }),
  useCreateAuditRecord: () => vi.fn(),
}))

describe('Legal and audit records', () => {
  it('validates legal effective/expiry date ordering', async () => {
    const user = userEvent.setup()
    render(<MemoryRouter initialEntries={['/risk-compliance/legal-records/new']}><Routes><Route path="/risk-compliance/legal-records/new" element={<LegalRecordDetailPage />} /></Routes></MemoryRouter>)
    await user.type(screen.getByLabelText('Record Code'), 'LC-1')
    await user.type(screen.getByLabelText('Title'), 'Contract')
    await user.type(screen.getByLabelText('Effective Date'), '2026-12-31')
    await user.type(screen.getByLabelText('Expiry Date'), '2026-01-01')
    await user.click(screen.getByRole('button', { name: 'Save Legal Record' }))
    expect(screen.getByText(/Expiry date must be after effective date/i)).toBeInTheDocument()
  })

  it('renders audit record findings and attachment link', () => {
    render(<MemoryRouter initialEntries={['/risk-compliance/audit-records/2']}><Routes><Route path="/risk-compliance/audit-records/:id" element={<AuditRecordDetailPage />} /></Routes></MemoryRouter>)
    expect(screen.getByText('Missing controls')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Attachment link' })).toBeInTheDocument()
  })
})
