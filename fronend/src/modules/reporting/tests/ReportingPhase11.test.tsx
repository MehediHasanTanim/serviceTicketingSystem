import { fireEvent, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { renderWithProviders } from '../../../test/utils'
import { DepartmentDashboardsPage, ExecutiveDashboardPage, ReportBuilderPage, ReportRunsPage, ReportSchedulesPage, ReportingAuditLogsPage } from '../pages'

vi.mock('../../../features/auth/authContext', async () => {
  const actual = await vi.importActual<typeof import('../../../features/auth/authContext')>('../../../features/auth/authContext')
  return { ...actual, useAuth: () => ({ auth: { accessToken: 'x', user: { org_id: 1 } } }) }
})
vi.mock('../hooks/useReporting', () => ({
  useExecutiveSummary: () => ({ loading: false, error: '', data: { open_tasks_by_module: { maintenance: 1 }, completed_tasks_by_module: { maintenance: 2 }, overdue_items_by_module: { maintenance: 0 }, average_resolution_hours: 3.5, total_operational_cost: 100, compliance_rate: 98, guest_satisfaction_score: 4.7, energy_efficiency_kpi: 10 }, reload: vi.fn() }),
  useReportingSla: () => ({ loading: false, error: '', data: { sla_compliance_percent: 66 }, reload: vi.fn() }),
  useReportingCosts: () => ({ loading: false, error: '', data: { total_operational_cost: 100 }, reload: vi.fn() }),
  useReportingCompliance: () => ({ loading: false, error: '', data: { compliance_rate: 98 }, reload: vi.fn() }),
  useReportingEnergy: () => ({ loading: false, error: '', data: { energy_efficiency_kpi: 10 }, reload: vi.fn() }),
  useDepartmentPerformance: () => ({ loading: false, error: '', data: { open_tasks_by_module: { maintenance: 2 }, completed_tasks_by_module: { maintenance: 1 }, overdue_items_by_module: { maintenance: 0 }, average_resolution_hours: 2, total_operational_cost: 50, compliance_rate: 90 } }),
  useReportDefinitions: () => ({ data: { results: [{ id: 1, name: 'Ops', report_code: 'OPS', report_type: 'OPERATIONAL_SUMMARY', is_active: true }] }, loading: false, error: '', reload: vi.fn() }),
  useReportDefinitionDetail: () => ({ data: null }),
  useCreateReportDefinition: () => vi.fn(async () => ({})),
  useUpdateReportDefinition: () => vi.fn(async () => ({})),
  useReportRuns: () => ({ data: { results: [{ id: 1, report_definition_id: 1, status: 'FAILED', output_format: 'PDF', created_at: new Date().toISOString(), completed_at: null, error_message: 'boom' }] }, reload: vi.fn() }),
  useRunReport: () => vi.fn(async () => ({ id: 2, status: 'RUNNING' })),
  useDownloadReport: () => vi.fn(async () => ({ file_path: '/tmp/report.pdf', size: 100 })),
  useReportRunDetail: () => ({ data: null, loading: false, error: '' }),
  useReportSchedules: () => ({ data: { results: [{ id: 2, name: 'Daily', frequency_type: 'DAILY', is_active: true, next_run_at: null, last_run_at: null }] }, reload: vi.fn() }),
  useCreateReportSchedule: () => vi.fn(async () => ({})),
  useUpdateReportSchedule: () => vi.fn(async () => ({})),
  useActivateReportSchedule: () => vi.fn(async () => ({})),
  useDeactivateReportSchedule: () => vi.fn(async () => ({})),
  useRunDueReportSchedules: () => vi.fn(async () => ({ schedules_checked: 1, reports_generated: 1, emails_sent: 1, failures: 0 })),
  useReportingAuditLogs: () => ({ loading: false, error: '', data: { count: 1, results: [{ id: 1, created_at: new Date().toISOString(), actor_user_id: 1, action: 'report_run_requested', target_type: 'report_run', target_id: '1', metadata: { foo: 'bar' } }] } }),
}))

describe('reporting widgets', () => {
  it('renders executive KPI cards with safe values', () => {
    renderWithProviders(<ExecutiveDashboardPage />, { route: '/reporting/executive-dashboard' })
    expect(screen.getByText('Average Resolution Hours')).toBeInTheDocument()
    expect(screen.getByText('3.50')).toBeInTheDocument()
  })

  it('renders department KPI and drill-down action', () => {
    renderWithProviders(<DepartmentDashboardsPage />, { route: '/reporting/departments' })
    expect(screen.getByText('Department KPI Dashboards')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Open module' })).toBeInTheDocument()
  })
})

describe('report builder state', () => {
  it('validates required fields', async () => {
    renderWithProviders(<ReportBuilderPage />, { route: '/reporting/report-builder' })
    fireEvent.change(screen.getByLabelText('report_code'), { target: { value: '' } })
    fireEvent.change(screen.getByLabelText('name'), { target: { value: '' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(await screen.findByText('report_code and name are required.')).toBeInTheDocument()
  })
})

describe('runs and schedules', () => {
  it('disables download until completed and shows failed run', () => {
    renderWithProviders(<ReportRunsPage />, { route: '/reporting/reports/runs' })
    expect(screen.getByText('boom')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Download' })).toBeDisabled()
  })

  it('validates schedule recipient emails', async () => {
    renderWithProviders(<ReportSchedulesPage />, { route: '/reporting/schedules' })
    fireEvent.change(screen.getByLabelText('schedule_report_definition_id'), { target: { value: '1' } })
    fireEvent.change(screen.getByLabelText('schedule_name'), { target: { value: 'Daily' } })
    fireEvent.change(screen.getByLabelText('schedule_recipients'), { target: { value: 'bad-email' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create Schedule' }))
    expect(await screen.findByText('Invalid recipient email.')).toBeInTheDocument()
  })
})

describe('audit logs', () => {
  it('opens metadata drawer', () => {
    renderWithProviders(<ReportingAuditLogsPage />, { route: '/reporting/audit-logs' })
    fireEvent.click(screen.getByRole('button', { name: 'Open' }))
    expect(screen.getByRole('heading', { name: 'Metadata' })).toBeInTheDocument()
    expect(screen.getByText(/"foo": "bar"/)).toBeInTheDocument()
  })
})
