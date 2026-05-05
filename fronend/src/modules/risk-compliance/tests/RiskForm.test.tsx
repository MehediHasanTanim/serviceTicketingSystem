import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { RiskFormPage } from '../pages/RiskFormPage'

const createRiskMock = vi.fn()

vi.mock('../../../features/auth/authContext', () => ({ useAuth: () => ({ auth: { accessToken: 'x', user: { org_id: 1 } } }) }))
vi.mock('../hooks/useRiskCompliance', () => ({
  useRiskDetail: () => ({ data: null }),
  useCreateRisk: () => createRiskMock,
  useUpdateRisk: () => vi.fn(),
}))

describe('Risk form', () => {
  it('validates ranges, auto-calculates inherent score and risk level, submits payload', async () => {
    const user = userEvent.setup()
    render(<MemoryRouter initialEntries={['/risk-compliance/risks/new']}><Routes><Route path="/risk-compliance/risks/new" element={<RiskFormPage />} /></Routes></MemoryRouter>)

    await user.type(screen.getByLabelText('Risk Code'), 'R-1')
    await user.type(screen.getByLabelText('Title'), 'Boiler Risk')
    await user.clear(screen.getByLabelText('Likelihood (1-5)'))
    await user.type(screen.getByLabelText('Likelihood (1-5)'), '5')
    await user.clear(screen.getByLabelText('Impact (1-5)'))
    await user.type(screen.getByLabelText('Impact (1-5)'), '4')

    expect(screen.getByLabelText('Inherent Score')).toHaveValue('20')
    expect(screen.getByLabelText('Risk Level')).toHaveValue('CRITICAL')

    await user.click(screen.getByRole('button', { name: 'Save Risk' }))
    expect(createRiskMock).toHaveBeenCalled()
    expect(createRiskMock.mock.calls[0][1].likelihood).toBe(5)
    expect(createRiskMock.mock.calls[0][1].impact).toBe(4)
  })
})
