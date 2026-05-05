import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ComplianceRequirementFormPage } from '../pages/ComplianceRequirementFormPage'

const createMock = vi.fn()
const updateMock = vi.fn()

vi.mock('../../../features/auth/authContext', () => ({ useAuth: () => ({ auth: { accessToken: 'x', user: { org_id: 1 } } }) }))
vi.mock('../hooks/useRiskCompliance', () => ({
  useComplianceRequirementDetail: () => ({ data: null }),
  useCreateComplianceRequirement: () => createMock,
  useUpdateComplianceRequirement: () => updateMock,
}))

describe('Compliance checklist workflow', () => {
  it('validates required fields, supports add/remove checklist item, and submits payload', async () => {
    const user = userEvent.setup()
    render(<MemoryRouter initialEntries={['/risk-compliance/requirements/new']}><Routes><Route path="/risk-compliance/requirements/new" element={<ComplianceRequirementFormPage />} /></Routes></MemoryRouter>)

    await user.click(screen.getByRole('button', { name: 'Save Requirement' }))
    expect(screen.getByText('Requirement code is required.')).toBeInTheDocument()

    const textboxes = screen.getAllByRole('textbox')
    await user.type(textboxes[0], 'RC-1')
    await user.type(textboxes[1], 'Fire Drill')
    await user.click(screen.getByRole('button', { name: 'Add Item' }))
    await user.click(screen.getAllByRole('button', { name: 'Remove' })[1])
    const itemTitleLabel = screen.getByText('Item Title').closest('label')
    const itemTitleInput = itemTitleLabel?.querySelector('input')
    if (!itemTitleInput) throw new Error('Item title input not found')
    await user.type(itemTitleInput, 'Upload evidence')
    await user.click(screen.getByRole('button', { name: 'Save Requirement' }))

    expect(createMock).toHaveBeenCalled()
    expect(createMock.mock.calls[0][1].checklist_items[0].title).toBe('Upload evidence')
  })
})
