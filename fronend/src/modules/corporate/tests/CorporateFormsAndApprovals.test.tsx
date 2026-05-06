import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { CapexForm, computePOLine, ContractForm, PurchaseOrderForm, SupplierForm } from '../components/forms'
import { ApprovalQueuePage } from '../pages'

const mockUseAuth = vi.fn()
const mockUseApprovalQueue = vi.fn()
const mockUseApprovalDecision = vi.fn()

vi.mock('../../../features/auth/authContext', () => ({ useAuth: () => mockUseAuth() }))
vi.mock('../hooks/useCorporate', async () => {
  const actual = await vi.importActual<any>('../hooks/useCorporate')
  return { ...actual, useApprovalQueue: (...args: any[]) => mockUseApprovalQueue(...args), useApprovalDecision: () => mockUseApprovalDecision }
})

describe('Corporate forms', () => {
  it('supplier validation + blacklisted warning + prefill', async () => {
    const onSubmit = vi.fn()
    render(<SupplierForm orgId={1} onSubmit={onSubmit} initial={{ id: 1, org_id: 1, supplier_code: 'SUP-1', name: 'Acme', contact_person: '', email: '', phone: '', address: '', tax_id: '', category: '', status: 'BLACKLISTED', rating: 4, notes: '', created_at: '', updated_at: '' }} />)
    expect(screen.getByText('Warning: this supplier is blacklisted.')).toBeInTheDocument()
    expect((screen.getByLabelText('Name') as HTMLInputElement).value).toBe('Acme')
    await userEvent.clear(screen.getByLabelText('Name'))
    await userEvent.click(screen.getByRole('button', { name: 'Save Supplier' }))
    expect(await screen.findByText('Name is required.')).toBeInTheDocument()
  })

  it('contract validation for dates/value and submit payload', async () => {
    const onSubmit = vi.fn()
    render(<ContractForm orgId={8} onSubmit={onSubmit} />)
    await userEvent.type(screen.getByLabelText('supplier_id'), '10')
    await userEvent.type(screen.getByLabelText('title'), 'Contract A')
    await userEvent.type(screen.getByLabelText('effective_date'), '2026-01-10')
    await userEvent.type(screen.getByLabelText('expiry_date'), '2026-01-01')
    await userEvent.clear(screen.getByLabelText('contract_value'))
    await userEvent.type(screen.getByLabelText('contract_value'), '-2')
    await userEvent.click(screen.getByRole('button', { name: 'Save Contract' }))
    expect(await screen.findByText('Expiry date must be after effective date.')).toBeInTheDocument()
    expect(await screen.findByText('Contract value cannot be negative.')).toBeInTheDocument()
  })

  it('purchase order line math and guards', async () => {
    expect(computePOLine({ item_name: 'X', description: '', quantity: '2', unit_price: '10', tax_rate: '0.1', discount_amount: '1' })).toBe(21)
    const onSubmit = vi.fn()
    render(<PurchaseOrderForm orgId={1} onSubmit={onSubmit} initial={{ id: 1, org_id: 1, po_number: 'PO-1', supplier_id: 1, contract_id: null, property_id: null, department_id: null, requester_id: 2, approver_id: null, secondary_approver_id: null, status: 'DRAFT', priority: 'MEDIUM', requested_date: null, required_by: null, approved_at: null, ordered_at: null, received_at: null, subtotal: '0', tax_amount: '0', discount_amount: '0', total_amount: '0', currency: 'USD', notes: '', line_items: [] }} />)
    await userEvent.click(screen.getByRole('button', { name: 'Save PO' }))
    expect(await screen.findByText('At least one line item is required.')).toBeInTheDocument()
  })

  it('capex high-value validation', async () => {
    const onSubmit = vi.fn()
    render(<CapexForm orgId={1} onSubmit={onSubmit} />)
    await userEvent.type(screen.getByLabelText('title'), 'New CAPEX')
    await userEvent.type(screen.getByLabelText('requester_id'), '4')
    await userEvent.type(screen.getByLabelText('estimated_amount'), '6000')
    await userEvent.type(screen.getByLabelText('approved_amount'), '1000')
    await userEvent.type(screen.getByLabelText('justification'), 'Need upgrade')
    await userEvent.click(screen.getByRole('button', { name: 'Save CAPEX' }))
    expect(await screen.findByText('Business impact is required for high-value CAPEX.')).toBeInTheDocument()
  })
})

describe('Approval interactions', () => {
  beforeEach(() => {
    mockUseAuth.mockReturnValue({ auth: { accessToken: 't', user: { org_id: 1 } } })
    mockUseApprovalDecision.mockReset().mockResolvedValue({})
    mockUseApprovalQueue.mockReturnValue({ data: { count: 2, results: [
      { id: 2, org_id: 1, entity_type: 'CAPEX_REQUEST', entity_id: 90, approval_level: 1, approver_id: 11, status: 'APPROVED', decision_comment: '', decided_at: '', created_at: '' },
      { id: 1, org_id: 1, entity_type: 'PURCHASE_ORDER', entity_id: 12, approval_level: 1, approver_id: 11, status: 'PENDING', decision_comment: '', decided_at: null, created_at: '' },
    ] }, error: '', reload: vi.fn() })
  })

  it('renders rows and pending first with actionable buttons', async () => {
    render(<ApprovalQueuePage />)
    const rows = screen.getAllByRole('row')
    expect(rows[1]).toHaveTextContent('PENDING')
    await userEvent.click(screen.getByRole('button', { name: 'Approve' }))
    expect(mockUseApprovalDecision).toHaveBeenCalled()
  })
})
