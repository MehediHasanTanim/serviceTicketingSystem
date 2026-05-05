import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useRiskComplianceDashboard } from '../hooks/useRiskCompliance'

export function RiskComplianceDashboardPage() {
  const { auth } = useAuth()
  const [params, setParams] = useSearchParams()
  const [withinDays, setWithinDays] = useState(Number(params.get('within_days') || 30))
  const { data, loading, error, reload } = useRiskComplianceDashboard(auth?.accessToken, auth?.user?.org_id, withinDays)

  const summary = data?.summary || { total_requirements: 0, compliant_checks: 0, non_compliant_checks: 0, overdue_checks: 0, compliance_rate: 0, open_risks: 0, critical_risks: 0, overdue_mitigations: 0, expiring_contracts: 0, audit_findings: 0 }
  const updateFilter = (days: number) => {
    setWithinDays(days)
    const next = new URLSearchParams(params)
    next.set('within_days', String(days))
    setParams(next, { replace: true })
  }

  return <div className="page full"><div className="glass panel"><div className="section-head"><h2>Risk & Compliance Dashboard</h2><label className="field" style={{ maxWidth: '220px' }}>Legal Expiry Window (days)<input className="input" type="number" value={withinDays} onChange={(e) => updateFilter(Number(e.target.value || 30))} /></label></div>
    {loading ? <p>Loading dashboard...</p> : null}
    {error ? <div><p className="error-text">{error}</p><button className="button secondary small" onClick={reload}>Retry</button></div> : null}
    <div className="cards-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '12px' }}>
      <div className="card-section"><strong>Total requirements</strong><div>{summary.total_requirements ?? 0}</div></div>
      <div className="card-section"><strong>Compliant checks</strong><div>{summary.compliant_checks ?? 0}</div></div>
      <div className="card-section"><strong>Non-compliant checks</strong><div>{summary.non_compliant_checks ?? 0}</div></div>
      <div className="card-section"><strong>Overdue checks</strong><div>{summary.overdue_checks ?? 0}</div></div>
      <div className="card-section"><strong>Compliance rate</strong><div>{summary.compliance_rate ?? 0}%</div></div>
      <div className="card-section"><strong>Open risks</strong><div>{summary.open_risks ?? 0}</div></div>
      <div className="card-section"><strong>Critical risks</strong><div>{summary.critical_risks ?? 0}</div></div>
      <div className="card-section"><strong>Overdue mitigations</strong><div>{summary.overdue_mitigations ?? 0}</div></div>
      <div className="card-section"><strong>Expiring contracts</strong><div>{summary.expiring_contracts ?? 0}</div></div>
      <div className="card-section"><strong>Audit findings</strong><div>{summary.audit_findings ?? 0}</div></div>
    </div>
    <div className="grid-form two" style={{ marginTop: '12px' }}>
      <div className="card-section"><h3>Compliance Status by Category/Property</h3><pre>{JSON.stringify(data?.complianceStatus || [], null, 2)}</pre></div>
      <div className="card-section"><h3>Risk Summary by Level</h3><pre>{JSON.stringify(data?.riskSummary || [], null, 2)}</pre></div>
    </div>
    <div className="card-section"><h3>Legal Expiry Timeline</h3><pre>{JSON.stringify(data?.legalExpiry || [], null, 2)}</pre></div>
  </div></div>
}
