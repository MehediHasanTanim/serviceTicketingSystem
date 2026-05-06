import { useMemo, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useBulkEnergyKPIReadingUpload, useCreateEnergyKPIReading, useCreateSustainabilityTarget, useCreateUtilityCost, useEnergyAuditLogs, useEnergyDashboard, useEnergyKPIReadingDetail, useEnergyKPIReadings, useEnergyTrends, useSustainabilityAnalytics, useSustainabilityTargets, useUpdateSustainabilityTarget, useUpdateUtilityCost, useUtilityCostAction, useUtilityCostDetail, useUtilityCosts } from '../hooks/useEnergy'
import type { Grouping, SustainabilityTargetStatus, UtilityCostStatus } from '../types/energy.types'

const safeNumber = (v: unknown) => {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}
const fmt = (v: unknown, d = 2) => safeNumber(v).toFixed(d)

const groupings: Grouping[] = ['day', 'week', 'month', 'quarter', 'year']

function DashboardFilters({ params, setParams }: { params: URLSearchParams; setParams: (next: URLSearchParams) => void }) {
  const update = (k: string, v: string) => {
    const next = new URLSearchParams(params)
    if (v) next.set(k, v)
    else next.delete(k)
    setParams(next)
  }
  return <div className='grid-form filters-grid'>
    <input aria-label='date_from' className='input' type='date' value={params.get('date_from') || ''} onChange={(e) => update('date_from', e.target.value)} />
    <input aria-label='date_to' className='input' type='date' value={params.get('date_to') || ''} onChange={(e) => update('date_to', e.target.value)} />
    <input aria-label='property_id' className='input' placeholder='Property' value={params.get('property_id') || ''} onChange={(e) => update('property_id', e.target.value)} />
    <input aria-label='department_id' className='input' placeholder='Department' value={params.get('department_id') || ''} onChange={(e) => update('department_id', e.target.value)} />
    <input aria-label='metric_type' className='input' placeholder='Metric Type' value={params.get('metric_type') || ''} onChange={(e) => update('metric_type', e.target.value)} />
    <input aria-label='utility_type' className='input' placeholder='Utility Type' value={params.get('utility_type') || ''} onChange={(e) => update('utility_type', e.target.value)} />
    <input aria-label='source' className='input' placeholder='Source' value={params.get('source') || ''} onChange={(e) => update('source', e.target.value)} />
    <select aria-label='grouping' className='input' value={params.get('grouping') || 'month'} onChange={(e) => update('grouping', e.target.value)}>{groupings.map((g) => <option key={g} value={g}>{g}</option>)}</select>
  </div>
}

export function EnergyDashboardPage() {
  const { auth } = useAuth()
  const [params, setParams] = useSearchParams()
  const q = useMemo(() => ({
    org_id: auth?.user?.org_id || 0,
    property_id: params.get('property_id') || undefined,
    department_id: params.get('department_id') || undefined,
    metric_type: params.get('metric_type') || undefined,
    utility_type: params.get('utility_type') || undefined,
    source: params.get('source') || undefined,
    grouping: (params.get('grouping') as Grouping) || 'month',
    date_from: params.get('date_from') || undefined,
    date_to: params.get('date_to') || undefined,
  }), [auth?.user?.org_id, params])
  const { data, loading, error, reload } = useEnergyDashboard(auth?.accessToken, q)
  const hasData = (data?.trends.results || []).length > 0
  return <div className='page full'><div className='glass panel'><div className='section-head'><h2>Energy Dashboard</h2><button className='button secondary small' onClick={reload}>Retry</button></div>
    <DashboardFilters params={params} setParams={setParams} />
    {loading ? <p className='helper'>Loading dashboard...</p> : null}
    {error ? <p className='error-text'>{error}</p> : null}
    {!loading && !error && !hasData ? <p className='hint'>No analytics data.</p> : null}
    <div className='cards-grid'>
      <article className='glass panel'><h3>Total energy usage</h3><p>{fmt(data?.summary.total_energy_usage)}</p></article>
      <article className='glass panel'><h3>Total water usage</h3><p>{fmt(data?.summary.total_water_usage)}</p></article>
      <article className='glass panel'><h3>Total carbon emissions</h3><p>{fmt(data?.summary.total_carbon_emissions)}</p></article>
      <article className='glass panel'><h3>Total utility cost</h3><p>{fmt(data?.summary.total_utility_cost)}</p></article>
      <article className='glass panel'><h3>Average energy per room night</h3><p>{fmt(data?.efficiency.average_energy_per_room_night, 4)}</p></article>
      <article className='glass panel'><h3>Average water per room night</h3><p>{fmt(data?.efficiency.average_water_per_room_night, 4)}</p></article>
      <article className='glass panel'><h3>Average cost per room night</h3><p>{fmt(data?.efficiency.average_cost_per_room_night, 4)}</p></article>
      <article className='glass panel'><h3>Energy per sqft</h3><p>{fmt(data?.efficiency.energy_per_sqft, 6)}</p></article>
      <article className='glass panel'><h3>Carbon per room night</h3><p>{fmt(data?.efficiency.carbon_per_room_night, 6)}</p></article>
      <article className='glass panel'><h3>Peak usage period</h3><p>{data?.trends.peak_usage_period?.period || '-'}</p></article>
      <article className='glass panel'><h3>Highest cost utility type</h3><p>{data?.costs.highest_cost_utility_type || '-'}</p></article>
    </div>
  </div></div>
}

export function EnergyTrendsPage() {
  const { auth } = useAuth()
  const [params, setParams] = useSearchParams()
  const [active, setActive] = useState<{ period: string; total: number | string } | null>(null)
  const q = useMemo(() => ({ org_id: auth?.user?.org_id || 0, property_id: params.get('property_id') || undefined, department_id: params.get('department_id') || undefined, metric_type: params.get('metric_type') || undefined, source: params.get('source') || undefined, grouping: (params.get('grouping') as Grouping) || 'month', date_from: params.get('date_from') || undefined, date_to: params.get('date_to') || undefined }), [auth?.user?.org_id, params])
  const { data, loading, error, reload } = useEnergyTrends(auth?.accessToken, q)
  return <div className='page full'><div className='glass panel'><div className='section-head'><h2>Energy Trends</h2><button className='button secondary small' onClick={reload}>Retry</button></div>
    <DashboardFilters params={params} setParams={setParams} />
    {loading ? <p>Loading trends...</p> : null}{error ? <p className='error-text'>{error}</p> : null}
    <div className='cards-grid'><article className='glass panel'><h3>MoM change</h3><p>{fmt(data?.month_over_month_change)}%</p></article><article className='glass panel'><h3>YoY change</h3><p>{fmt(data?.year_over_year_change)}%</p></article></div>
    <div className='table-wrap'><table className='data-table'><thead><tr><th>Period</th><th>Total</th><th>Actions</th></tr></thead><tbody>{(data?.results || []).map((r) => <tr key={r.period}><td>{r.period}</td><td>{fmt(r.total, 6)}</td><td><button className='button secondary small' onClick={() => setActive(r)}>Detail</button></td></tr>)}</tbody></table></div>
    {active ? <div className='card-section'><h3>Detail Drawer</h3><p>Period: {active.period}</p><p>Total: {fmt(active.total, 6)}</p><button className='button secondary small' onClick={() => setActive(null)}>Close</button></div> : null}
  </div></div>
}

export function KPIReadingsPage() {
  const { auth } = useAuth(); const nav = useNavigate(); const [params, setParams] = useSearchParams()
  const q = useMemo(() => ({ org_id: auth?.user?.org_id || 0, page: Number(params.get('page') || 1), page_size: Number(params.get('page_size') || 10), property_id: params.get('property_id') || undefined, department_id: params.get('department_id') || undefined, metric_type: params.get('metric_type') || undefined, source: params.get('source') || undefined, date_from: params.get('date_from') || undefined, date_to: params.get('date_to') || undefined, q: params.get('q') || undefined }), [auth?.user?.org_id, params])
  const { data, loading, error } = useEnergyKPIReadings(auth?.accessToken, q)
  const pages = Math.max(1, Math.ceil((data?.count || 0) / (q.page_size || 10)))
  const update = (k: string, v: string) => { const next = new URLSearchParams(params); if (v) next.set(k, v); else next.delete(k); if (k !== 'page') next.set('page', '1'); setParams(next) }
  return <div className='page full'><div className='glass panel'><div className='section-head'><h2>KPI Readings</h2><button className='button' onClick={() => nav('/energy/kpi-readings/new')}>New</button></div>
    <div className='grid-form three'><input aria-label='property' className='input' placeholder='property_id' value={params.get('property_id') || ''} onChange={(e) => update('property_id', e.target.value)} /><input aria-label='department' className='input' placeholder='department_id' value={params.get('department_id') || ''} onChange={(e) => update('department_id', e.target.value)} /><input aria-label='metric_type' className='input' placeholder='metric_type' value={params.get('metric_type') || ''} onChange={(e) => update('metric_type', e.target.value)} /><input aria-label='source' className='input' placeholder='source' value={params.get('source') || ''} onChange={(e) => update('source', e.target.value)} /><input aria-label='external_reference' className='input' placeholder='external reference' value={params.get('q') || ''} onChange={(e) => update('q', e.target.value)} /><input aria-label='date_from' className='input' type='date' value={params.get('date_from') || ''} onChange={(e) => update('date_from', e.target.value)} /></div>
    {loading ? <p>Loading readings...</p> : null}{error ? <p className='error-text'>{error}</p> : null}
    <div className='table-wrap'><table className='data-table'><thead><tr><th>Reading Date</th><th>Property</th><th>Department</th><th>Metric Type</th><th>Source</th><th>Raw Value / Unit</th><th>Normalized Value / Unit</th><th>Period Start</th><th>Period End</th><th>Ingested By</th><th>Created At</th></tr></thead><tbody>{(data?.results || []).map((r) => <tr key={r.id} onClick={() => nav(`/energy/kpi-readings/${r.id}`)}><td>{r.reading_date}</td><td>{r.property_id}</td><td>{r.department_id || '-'}</td><td>{r.metric_type}</td><td>{r.source}</td><td>{fmt(r.raw_value, 6)} {r.raw_unit}</td><td>{fmt(r.normalized_value, 6)} {r.normalized_unit}</td><td>{new Date(r.period_start).toLocaleString()}</td><td>{new Date(r.period_end).toLocaleString()}</td><td>{r.ingested_by || '-'}</td><td>{new Date(r.created_at).toLocaleString()}</td></tr>)}</tbody></table></div>
    <div className='pagination-row'><button className='button secondary small' disabled={q.page <= 1} onClick={() => update('page', String(q.page - 1))}>Prev</button><span>Page {q.page} of {pages}</span><button className='button secondary small' disabled={q.page >= pages} onClick={() => update('page', String(q.page + 1))}>Next</button></div>
  </div></div>
}

export function KPIReadingFormPage() {
  const { auth } = useAuth(); const { id } = useParams(); const nav = useNavigate(); const create = useCreateEnergyKPIReading(); const bulk = useBulkEnergyKPIReadingUpload(); const detail = useEnergyKPIReadingDetail(auth?.accessToken, id ? Number(id) : undefined, auth?.user?.org_id)
  const [form, setForm] = useState<any>({ property_id: '', department_id: '', meter_id: '', source: 'MANUAL', reading_date: '', period_start: '', period_end: '', metric_type: 'ELECTRICITY', raw_value: '0', raw_unit: '', occupancy_count: '', room_nights: '', covers_count: '', area_sqft: '', external_reference_id: '', metadata: '{}' })
  const [error, setError] = useState(''); const [saving, setSaving] = useState(false)
  const submit = async () => {
    if (!auth?.accessToken || !auth.user?.org_id) return
    if (Number(form.raw_value) < 0) return setError('raw_value must be non-negative')
    if (new Date(form.period_end).getTime() <= new Date(form.period_start).getTime()) return setError('period_end must be after period_start')
    setSaving(true); setError('')
    try {
      const payload = { org_id: auth.user.org_id, property_id: Number(form.property_id), department_id: form.department_id ? Number(form.department_id) : null, meter_id: form.meter_id ? Number(form.meter_id) : null, source: form.source, reading_date: form.reading_date, period_start: form.period_start, period_end: form.period_end, metric_type: form.metric_type, raw_value: form.raw_value, raw_unit: form.raw_unit, occupancy_count: form.occupancy_count ? Number(form.occupancy_count) : null, room_nights: form.room_nights ? Number(form.room_nights) : null, covers_count: form.covers_count ? Number(form.covers_count) : null, area_sqft: form.area_sqft || null, external_reference_id: form.external_reference_id || '', metadata: JSON.parse(form.metadata || '{}') }
      await create(auth.accessToken, payload)
      nav('/energy/kpi-readings')
    } catch (e: any) { setError(e?.message || 'Save failed') } finally { setSaving(false) }
  }
  const seedBulk = async () => { if (!auth?.accessToken || !auth.user?.org_id) return; await bulk(auth.accessToken, { org_id: auth.user.org_id, items: [] }) }
  const row = detail.data
  return <div className='page full'><div className='glass panel'><h2>{id ? 'KPI Reading Detail' : 'New KPI Reading'}</h2>
    {id && row ? <pre>{JSON.stringify(row, null, 2)}</pre> : <div className='grid-form two'>{['property_id','department_id','meter_id','source','reading_date','period_start','period_end','metric_type','raw_value','raw_unit','occupancy_count','room_nights','covers_count','area_sqft','external_reference_id','metadata'].map((k) => <label className='field' key={k}>{k}<input aria-label={k} className='input' value={form[k]} onChange={(e) => setForm((p: any) => ({ ...p, [k]: e.target.value }))} /></label>)}</div>}
    {error ? <p className='error-text'>{error}</p> : null}
    {!id ? <div className='actions-row'><button className='button' onClick={submit} disabled={saving}>{saving ? 'Saving...' : 'Submit'}</button><button className='button secondary small' onClick={seedBulk}>Bulk Upload</button></div> : null}
  </div></div>
}

const utilityAllowed = (status: UtilityCostStatus) => ({ submit: status === 'DRAFT', approve: status === 'SUBMITTED', paid: status === 'APPROVED', void: status !== 'VOID' && status !== 'PAID' })

export function UtilityCostsPage() {
  const { auth } = useAuth(); const nav = useNavigate(); const [params, setParams] = useSearchParams(); const [confirm, setConfirm] = useState<{ id: number; action: '' | 'submit' | 'approve' | 'mark-paid' | 'void' }>({ id: 0, action: '' })
  const q = useMemo(() => ({ org_id: auth?.user?.org_id || 0, page: Number(params.get('page') || 1), page_size: 10, property_id: params.get('property_id') || undefined, department_id: params.get('department_id') || undefined, utility_type: params.get('utility_type') || undefined, status: params.get('status') || undefined, vendor_id: params.get('vendor_id') || undefined, date_from: params.get('date_from') || undefined, date_to: params.get('date_to') || undefined }), [auth?.user?.org_id, params])
  const { data, loading, error, reload } = useUtilityCosts(auth?.accessToken, q)
  const action = useUtilityCostAction()
  const update = (k: string, v: string) => { const next = new URLSearchParams(params); if (v) next.set(k, v); else next.delete(k); if (k !== 'page') next.set('page', '1'); setParams(next) }
  const run = async () => { if (!auth?.accessToken || !auth.user?.org_id || !confirm.action) return; await action(auth.accessToken, confirm.id, confirm.action, { org_id: auth.user.org_id }); setConfirm({ id: 0, action: '' }); await reload() }
  return <div className='page full'><div className='glass panel'><div className='section-head'><h2>Utility Costs</h2><button className='button' onClick={() => nav('/energy/utility-costs/new')}>New</button></div>
    <div className='grid-form three'>{['property_id','department_id','utility_type','status','vendor_id','date_from'].map((k) => <input key={k} className='input' value={params.get(k) || ''} onChange={(e) => update(k, e.target.value)} placeholder={k} />)}</div>
    {loading ? <p>Loading utility costs...</p> : null}{error ? <p className='error-text'>{error}</p> : null}
    <div className='table-wrap'><table className='data-table'><thead><tr><th>Billing Period</th><th>Property</th><th>Department</th><th>Utility Type</th><th>Vendor</th><th>Usage</th><th>Total Cost</th><th>Currency</th><th>Status</th><th>Invoice Number</th><th>Updated At</th><th>Actions</th></tr></thead><tbody>{(data?.results || []).map((r) => { const can = utilityAllowed(r.status); return <tr key={r.id}><td>{r.billing_period_start} - {r.billing_period_end}</td><td>{r.property_id}</td><td>{r.department_id || '-'}</td><td>{r.utility_type}</td><td>{r.vendor_id || '-'}</td><td>{fmt(r.usage_value, 6)} {r.usage_unit}</td><td>{fmt(r.total_cost)}</td><td>{r.currency}</td><td><span className='badge neutral'>{r.status}</span></td><td>{r.invoice_number || '-'}</td><td>{new Date(r.updated_at).toLocaleString()}</td><td><div className='row-actions'><button className='button secondary small' onClick={() => nav(`/energy/utility-costs/${r.id}`)}>Open</button>{can.submit ? <button className='button secondary small' onClick={() => setConfirm({ id: r.id, action: 'submit' })}>Submit</button> : null}{can.approve ? <button className='button secondary small' onClick={() => setConfirm({ id: r.id, action: 'approve' })}>Approve</button> : null}{can.paid ? <button className='button secondary small' onClick={() => setConfirm({ id: r.id, action: 'mark-paid' })}>Mark Paid</button> : null}{can.void ? <button className='button secondary small' onClick={() => setConfirm({ id: r.id, action: 'void' })}>Void</button> : null}</div></td></tr> })}</tbody></table></div>
    {confirm.action ? <div className='modal-backdrop' role='presentation'><div className='modal' role='dialog' aria-modal='true' aria-label='Utility action confirmation'><p>Confirm {confirm.action} action?</p><div className='modal-actions'><button className='button secondary small' onClick={() => setConfirm({ id: 0, action: '' })}>Cancel</button><button className='button small' onClick={() => void run()}>Confirm</button></div></div></div> : null}
  </div></div>
}

export function UtilityCostFormPage() {
  const { auth } = useAuth(); const { id } = useParams(); const nav = useNavigate(); const edit = !!id; const create = useCreateUtilityCost(); const update = useUpdateUtilityCost(); const detail = useUtilityCostDetail(auth?.accessToken, id ? Number(id) : undefined, auth?.user?.org_id)
  const [f, setF] = useState<any>({ property_id: '', department_id: '', vendor_id: '', utility_type: 'ELECTRICITY', billing_period_start: '', billing_period_end: '', usage_value: '0', usage_unit: '', base_charge: '0', variable_charge: '0', tax_amount: '0', adjustment_amount: '0', currency: 'USD', invoice_number: '', attachment_id: '' })
  const total = safeNumber(f.base_charge) + safeNumber(f.variable_charge) + safeNumber(f.tax_amount) + safeNumber(f.adjustment_amount)
  const [error, setError] = useState(''); const [saving, setSaving] = useState(false)
  const submit = async () => {
    if (!auth?.accessToken || !auth.user?.org_id) return
    if (new Date(f.billing_period_end).getTime() <= new Date(f.billing_period_start).getTime()) return setError('billing_period_end must be after billing_period_start')
    if (safeNumber(f.usage_value) < 0 || safeNumber(f.base_charge) < 0 || safeNumber(f.variable_charge) < 0 || safeNumber(f.tax_amount) < 0) return setError('charges must be non-negative')
    const payload = { org_id: auth.user.org_id, property_id: Number(f.property_id), department_id: f.department_id ? Number(f.department_id) : null, vendor_id: f.vendor_id ? Number(f.vendor_id) : null, utility_type: f.utility_type, billing_period_start: f.billing_period_start, billing_period_end: f.billing_period_end, usage_value: f.usage_value, usage_unit: f.usage_unit, base_charge: f.base_charge, variable_charge: f.variable_charge, tax_amount: f.tax_amount, adjustment_amount: f.adjustment_amount, currency: f.currency, invoice_number: f.invoice_number, attachment_id: f.attachment_id ? Number(f.attachment_id) : null }
    setSaving(true); setError('')
    try { if (edit) await update(auth.accessToken, Number(id), payload); else await create(auth.accessToken, payload); nav('/energy/utility-costs') } catch (e: any) { setError(e?.message || 'Failed to save') } finally { setSaving(false) }
  }
  return <div className='page full'><div className='glass panel'><h2>{edit ? 'Utility Cost Detail' : 'New Utility Cost'}</h2>
    {edit && detail.data ? <pre>{JSON.stringify(detail.data, null, 2)}</pre> : <div className='grid-form two'>{['property_id','department_id','vendor_id','utility_type','billing_period_start','billing_period_end','usage_value','usage_unit','base_charge','variable_charge','tax_amount','adjustment_amount','currency','invoice_number','attachment_id'].map((k) => <label className='field' key={k}>{k}<input className='input' value={f[k]} onChange={(e) => setF((p: any) => ({ ...p, [k]: e.target.value }))} /></label>)}</div>}
    {!edit ? <p>Total Cost (auto): {fmt(total)}</p> : null}
    {error ? <p className='error-text'>{error}</p> : null}
    {!edit ? <button className='button' disabled={saving} onClick={() => void submit()}>{saving ? 'Saving...' : 'Submit'}</button> : null}
  </div></div>
}

const targetBadge = (s: SustainabilityTargetStatus) => s === 'ACHIEVED' ? 'success' : s === 'MISSED' ? 'critical' : 'neutral'

export function SustainabilityReportsPage() {
  const { auth } = useAuth(); const [params, setParams] = useSearchParams(); const q = useMemo(() => ({ org_id: auth?.user?.org_id || 0, property_id: params.get('property_id') || undefined, department_id: params.get('department_id') || undefined, metric_type: params.get('metric_type') || undefined, date_from: params.get('date_from') || undefined, date_to: params.get('date_to') || undefined }), [auth?.user?.org_id, params])
  const { data, loading, error } = useSustainabilityAnalytics(auth?.accessToken, q)
  const update = (k: string, v: string) => { const next = new URLSearchParams(params); if (v) next.set(k, v); else next.delete(k); setParams(next) }
  return <div className='page full'><div className='glass panel'><h2>Sustainability Reports</h2>
    <div className='grid-form three'>{['date_from','date_to','property_id','department_id','metric_type'].map((k) => <input key={k} className='input' value={params.get(k) || ''} onChange={(e) => update(k, e.target.value)} placeholder={k} />)}</div>
    {loading ? <p>Loading sustainability report...</p> : null}{error ? <p className='error-text'>{error}</p> : null}
    <div className='table-wrap'><table className='data-table'><thead><tr><th>Target</th><th>Status</th><th>Progress</th><th>Actual</th><th>Target Value</th></tr></thead><tbody>{(data?.targets || []).map((t) => <tr key={t.target_id}><td>{t.target_id}</td><td><span className={`badge ${targetBadge(t.computed_status)}`}>{t.computed_status}</span></td><td>{fmt(t.progress_pct)}%</td><td>{fmt(t.actual_value, 6)}</td><td>{fmt(t.target_value, 6)}</td></tr>)}</tbody></table></div>
  </div></div>
}

export function SustainabilityTargetsPage() {
  const { auth } = useAuth(); const nav = useNavigate(); const [params, setParams] = useSearchParams(); const q = useMemo(() => ({ org_id: auth?.user?.org_id || 0, property_id: params.get('property_id') || undefined, metric_type: params.get('metric_type') || undefined }), [auth?.user?.org_id, params])
  const { data, loading, error } = useSustainabilityTargets(auth?.accessToken, q)
  const update = (k: string, v: string) => { const n = new URLSearchParams(params); if (v) n.set(k, v); else n.delete(k); setParams(n) }
  return <div className='page full'><div className='glass panel'><div className='section-head'><h2>Sustainability Targets</h2><button className='button' onClick={() => nav('/energy/sustainability-targets/new')}>New</button></div>
    <div className='grid-form'><input className='input' value={params.get('property_id') || ''} placeholder='property_id' onChange={(e) => update('property_id', e.target.value)} /><input className='input' value={params.get('metric_type') || ''} placeholder='metric_type' onChange={(e) => update('metric_type', e.target.value)} /></div>
    {loading ? <p>Loading...</p> : null}{error ? <p className='error-text'>{error}</p> : null}
    <div className='table-wrap'><table className='data-table'><thead><tr><th>Property</th><th>Metric</th><th>Period</th><th>Target</th><th>Status</th><th>Dates</th><th>Actions</th></tr></thead><tbody>{(data?.results || []).map((r) => <tr key={r.id}><td>{r.property_id}</td><td>{r.metric_type}</td><td>{r.target_period}</td><td>{fmt(r.target_value, 6)} {r.target_unit}</td><td><span className={`badge ${targetBadge(r.status)}`}>{r.status}</span></td><td>{r.start_date} - {r.end_date}</td><td><button className='button secondary small' onClick={() => nav(`/energy/sustainability-targets/${r.id}/edit`)}>Edit</button></td></tr>)}</tbody></table></div>
  </div></div>
}

export function SustainabilityTargetFormPage() {
  const { auth } = useAuth(); const { id } = useParams(); const nav = useNavigate(); const edit = !!id; const create = useCreateSustainabilityTarget(); const update = useUpdateSustainabilityTarget(); const list = useSustainabilityTargets(auth?.accessToken, { org_id: auth?.user?.org_id || 0 })
  const target = (list.data?.results || []).find((x) => x.id === Number(id))
  const [f, setF] = useState<any>({ property_id: '', metric_type: 'ELECTRICITY', target_period: 'MONTH', target_value: '', target_unit: '', start_date: '', end_date: '', status: 'ACTIVE' })
  const [error, setError] = useState(''); const [saving, setSaving] = useState(false)
  const submit = async () => {
    if (!auth?.accessToken || !auth.user?.org_id) return
    if (safeNumber(f.target_value) <= 0) return setError('target_value must be positive')
    if (new Date(f.end_date).getTime() <= new Date(f.start_date).getTime()) return setError('end_date must be after start_date')
    const body = { org_id: auth.user.org_id, property_id: Number(f.property_id), metric_type: f.metric_type, target_period: f.target_period, target_value: f.target_value, target_unit: f.target_unit, start_date: f.start_date, end_date: f.end_date, status: f.status }
    setSaving(true); setError('')
    try { if (edit) await update(auth.accessToken, Number(id), body); else await create(auth.accessToken, body); nav('/energy/sustainability-targets') } catch (e: any) { setError(e?.message || 'Failed to save target') } finally { setSaving(false) }
  }
  return <div className='page full'><div className='glass panel'><h2>{edit ? 'Edit Sustainability Target' : 'New Sustainability Target'}</h2>
    {edit && target ? <pre>{JSON.stringify(target, null, 2)}</pre> : <div className='grid-form two'>{['property_id','metric_type','target_period','target_value','target_unit','start_date','end_date','status'].map((k) => <label className='field' key={k}>{k}<input aria-label={k} className='input' value={f[k]} onChange={(e) => setF((p: any) => ({ ...p, [k]: e.target.value }))} /></label>)}</div>}
    {error ? <p className='error-text'>{error}</p> : null}
    {!edit ? <button className='button' disabled={saving} onClick={() => void submit()}>{saving ? 'Saving...' : 'Submit'}</button> : null}
  </div></div>
}

export function EnergyAuditLogsPage() {
  const { auth } = useAuth(); const [params, setParams] = useSearchParams(); const [meta, setMeta] = useState<Record<string, unknown> | null>(null)
  const q = useMemo(() => ({ org_id: auth?.user?.org_id || 0, page: Number(params.get('page') || 1), page_size: 20, sort_by: params.get('sort_by') || 'created_at', sort_dir: params.get('sort_dir') || 'desc', actor_user_id: params.get('actor_user_id') || undefined, action: params.get('action') || undefined, target_type: params.get('target_type') || undefined, property_id: params.get('property_id') || undefined, metric_type: params.get('metric_type') || undefined, utility_type: params.get('utility_type') || undefined, date_from: params.get('date_from') || undefined, date_to: params.get('date_to') || undefined }), [auth?.user?.org_id, params])
  const { data, loading, error } = useEnergyAuditLogs(auth?.accessToken, q)
  const pages = Math.max(1, Math.ceil((data?.count || 0) / (q.page_size || 20)))
  const update = (k: string, v: string) => { const next = new URLSearchParams(params); if (v) next.set(k, v); else next.delete(k); if (k !== 'page') next.set('page', '1'); setParams(next) }
  return <div className='page full'><div className='glass panel'><h2>Energy Audit Logs</h2>
    <div className='grid-form three'>{['actor_user_id','action','target_type','property_id','metric_type','utility_type','date_from','date_to'].map((k) => <input key={k} className='input' value={params.get(k) || ''} onChange={(e) => update(k, e.target.value)} placeholder={k} />)}</div>
    {loading ? <p>Loading logs...</p> : null}{error ? <p className='error-text'>{error}</p> : null}
    <div className='table-wrap'><table className='data-table'><thead><tr><th>Timestamp</th><th>Actor</th><th>Action</th><th>Entity type</th><th>Entity ID</th><th>Metadata</th></tr></thead><tbody>{(data?.results || []).map((r) => <tr key={r.id}><td>{new Date(r.created_at).toLocaleString()}</td><td>{r.actor_user_id || '-'}</td><td>{r.action}</td><td>{r.target_type}</td><td>{r.target_id}</td><td><button className='button secondary small' onClick={() => setMeta(r.metadata || {})}>Open</button></td></tr>)}</tbody></table></div>
    <div className='pagination-row'><button className='button secondary small' disabled={q.page <= 1} onClick={() => update('page', String(q.page - 1))}>Prev</button><span>Page {q.page} of {pages}</span><button className='button secondary small' disabled={q.page >= pages} onClick={() => update('page', String(q.page + 1))}>Next</button></div>
    {meta ? <div className='card-section'><h3>Metadata</h3><pre>{JSON.stringify(meta, null, 2)}</pre><button className='button secondary small' onClick={() => setMeta(null)}>Close</button></div> : null}
  </div></div>
}
