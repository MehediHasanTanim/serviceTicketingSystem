import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { EnergyAuditLogsPage, EnergyDashboardPage, EnergyTrendsPage, KPIReadingFormPage, SustainabilityReportsPage, UtilityCostFormPage } from '../pages'

vi.mock('../../../features/auth/authContext', () => ({
  useAuth: () => ({ auth: { accessToken: 'token', user: { org_id: 1 } } }),
}))

vi.mock('../hooks/useEnergy', () => ({
  useEnergyDashboard: () => ({ loading: false, error: '', reload: vi.fn(), data: { summary: { total_energy_usage: '10' }, efficiency: { average_energy_per_room_night: '2' }, costs: { highest_cost_utility_type: 'WATER' }, trends: { results: [{ period: '2026-01', total: '1' }], peak_usage_period: { period: '2026-01', total: '1' } } } }),
  useEnergyTrends: () => ({ loading: false, error: '', reload: vi.fn(), data: { grouping: 'month', results: [{ period: '2026-01', total: '5' }], month_over_month_change: '10', year_over_year_change: '20' } }),
  useEnergyKPIReadingDetail: () => ({ data: null }),
  useCreateEnergyKPIReading: () => vi.fn(async () => ({ id: 1 })),
  useBulkEnergyKPIReadingUpload: () => vi.fn(async () => ({ count: 0, created: 0, results: [] })),
  useCreateUtilityCost: () => vi.fn(async () => ({ id: 1 })),
  useUpdateUtilityCost: () => vi.fn(async () => ({ id: 1 })),
  useUtilityCostDetail: () => ({ data: null }),
  useSustainabilityAnalytics: () => ({ loading: false, error: '', data: { targets: [{ target_id: 1, computed_status: 'ACHIEVED', progress_pct: 100, actual_value: 10, target_value: 10 }] } }),
  useEnergyAuditLogs: () => ({ loading: false, error: '', data: { count: 1, results: [{ id: 1, created_at: '2026-05-01T00:00:00Z', actor_user_id: 9, action: 'utility_cost_created', target_type: 'utility_cost_record', target_id: '1', metadata: { a: 1 } }] } }),
}))

describe('Energy Module UI', () => {
  it('renders dashboard KPI cards with safe values', () => {
    render(<MemoryRouter initialEntries={['/energy/dashboard']}><Routes><Route path='/energy/dashboard' element={<EnergyDashboardPage />} /></Routes></MemoryRouter>)
    expect(screen.getByText('Total energy usage')).toBeInTheDocument()
    expect(screen.getByText('10.00')).toBeInTheDocument()
  })

  it('grouping selector updates query params', () => {
    render(<MemoryRouter initialEntries={['/energy/dashboard?grouping=month']}><Routes><Route path='/energy/dashboard' element={<EnergyDashboardPage />} /></Routes></MemoryRouter>)
    const grouping = screen.getByLabelText('grouping') as HTMLSelectElement
    fireEvent.change(grouping, { target: { value: 'year' } })
    expect(grouping.value).toBe('year')
  })

  it('trend detail opens on chart-row action', () => {
    render(<MemoryRouter initialEntries={['/energy/trends']}><Routes><Route path='/energy/trends' element={<EnergyTrendsPage />} /></Routes></MemoryRouter>)
    fireEvent.click(screen.getByRole('button', { name: 'Detail' }))
    expect(screen.getByText('Detail Drawer')).toBeInTheDocument()
  })

  it('kpi reading form validates invalid period dates', async () => {
    render(<MemoryRouter initialEntries={['/energy/kpi-readings/new']}><Routes><Route path='/energy/kpi-readings/new' element={<KPIReadingFormPage />} /></Routes></MemoryRouter>)
    fireEvent.change(screen.getByLabelText('property_id'), { target: { value: '1' } })
    fireEvent.change(screen.getByLabelText('reading_date'), { target: { value: '2026-05-01' } })
    fireEvent.change(screen.getByLabelText('period_start'), { target: { value: '2026-05-02T00:00:00Z' } })
    fireEvent.change(screen.getByLabelText('period_end'), { target: { value: '2026-05-01T00:00:00Z' } })
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }))
    expect(await screen.findByText('period_end must be after period_start')).toBeInTheDocument()
  })

  it('utility form auto-calculates total and validates period', async () => {
    render(<MemoryRouter initialEntries={['/energy/utility-costs/new']}><Routes><Route path='/energy/utility-costs/new' element={<UtilityCostFormPage />} /></Routes></MemoryRouter>)
    expect(screen.getByText(/Total Cost \(auto\):/)).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('billing_period_start'), { target: { value: '2026-05-10' } })
    fireEvent.change(screen.getByLabelText('billing_period_end'), { target: { value: '2026-05-09' } })
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }))
    expect(await screen.findByText('billing_period_end must be after billing_period_start')).toBeInTheDocument()
  })

  it('audit log metadata drawer opens', () => {
    render(<MemoryRouter initialEntries={['/energy/audit-logs']}><Routes><Route path='/energy/audit-logs' element={<EnergyAuditLogsPage />} /></Routes></MemoryRouter>)
    fireEvent.click(screen.getByRole('button', { name: 'Open' }))
    expect(screen.getByRole('heading', { name: 'Metadata' })).toBeInTheDocument()
  })

  it('sustainability KPI cards render', () => {
    render(<MemoryRouter initialEntries={['/energy/sustainability']}><Routes><Route path='/energy/sustainability' element={<SustainabilityReportsPage />} /></Routes></MemoryRouter>)
    expect(screen.getByText('ACHIEVED')).toBeInTheDocument()
  })
})
