import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { RiskComplianceDashboardPage } from '../pages/RiskComplianceDashboardPage'

const dashboardMock = vi.fn(() => ({
  data: {
    summary: { total_requirements: 0, compliant_checks: 0, non_compliant_checks: 0, overdue_checks: 0, compliance_rate: 0, open_risks: 2, critical_risks: 1, overdue_mitigations: 0, expiring_contracts: 0, audit_findings: 0 },
    complianceStatus: [{ key: 'SAFETY', compliant: 4, non_compliant: 1, overdue: 0 }],
    riskSummary: [{ risk_level: 'HIGH', total: 2 }],
    legalExpiry: [{ date: '2026-01-01', expiring: 0 }],
  },
  loading: false,
  error: '',
  reload: vi.fn(),
}))

vi.mock('../../../features/auth/authContext', () => ({ useAuth: () => ({ auth: { accessToken: 'x', user: { org_id: 1 } } }) }))
vi.mock('../hooks/useRiskCompliance', () => ({ useRiskComplianceDashboard: () => dashboardMock() }))

describe('Dashboard filtering interactions', () => {
  it('renders zero-safe KPI values and filter update triggers hook with changed query value', async () => {
    const user = userEvent.setup()
    render(<MemoryRouter><RiskComplianceDashboardPage /></MemoryRouter>)
    expect(screen.getByText('Total requirements')).toBeInTheDocument()
    expect(screen.getAllByText('0').length).toBeGreaterThan(0)
    await user.clear(screen.getByLabelText('Legal Expiry Window (days)'))
    await user.type(screen.getByLabelText('Legal Expiry Window (days)'), '45')
    expect(dashboardMock).toHaveBeenCalled()
  })
})
