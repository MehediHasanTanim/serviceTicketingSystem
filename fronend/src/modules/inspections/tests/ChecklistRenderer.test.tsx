import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ChecklistRenderer } from '../components/ExecutionForm/ChecklistRenderer'

const sections = [{ id: 1, title: 'S1', description: '', sort_order: 1, weight: '1', items: [{ id: 10, question: 'Q1', description: '', response_type: 'PASS_FAIL_NA' as const, is_required: true, weight: '1', sort_order: 1, non_compliance_trigger: true }] }]

describe('ChecklistRenderer', () => {
  it('renders required and non-compliance indicators', () => {
    render(<ChecklistRenderer sections={sections} responses={{}} setResponses={vi.fn()} readOnly={false} />)
    expect(screen.getByLabelText('required')).toBeInTheDocument()
    expect(screen.getByText('NCR')).toBeInTheDocument()
  })

  it('updates selection PASS/FAIL/NA', async () => {
    const user = userEvent.setup()
    const setResponses = vi.fn()
    render(<ChecklistRenderer sections={sections} responses={{ 10: { response: '', comment: '', evidence_attachment_id: '' } }} setResponses={setResponses} readOnly={false} />)
    await user.click(screen.getByLabelText('FAIL'))
    expect(setResponses).toHaveBeenCalled()
  })
})
