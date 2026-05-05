import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { TemplateBuilder } from '../components/TemplateBuilder/TemplateBuilder'

describe('TemplateBuilder', () => {
  it('adds and deletes section with confirmation for non-empty section', async () => {
    const user = userEvent.setup()
    const setSections = vi.fn()
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
    render(<TemplateBuilder sections={[{ title: 'A', description: '', sort_order: 1, weight: '1', items: [{ question: 'Q', description: '', response_type: 'PASS_FAIL_NA', is_required: false, weight: '1', sort_order: 1, non_compliance_trigger: false }] }]} setSections={setSections} />)
    await user.click(screen.getByRole('button', { name: 'Add Section' }))
    expect(setSections).toHaveBeenCalled()
    await user.click(screen.getAllByRole('button', { name: 'Delete' })[0])
    expect(confirmSpy).toHaveBeenCalled()
  })

  it('prevents negative weight', async () => {
    const user = userEvent.setup()
    const setSections = vi.fn()
    render(<TemplateBuilder sections={[{ title: 'A', description: '', sort_order: 1, weight: '1', items: [] }]} setSections={setSections} />)
    await user.clear(screen.getByLabelText('Section weight'))
    await user.type(screen.getByLabelText('Section weight'), '-5')
    expect(setSections).toHaveBeenCalled()
  })
})
