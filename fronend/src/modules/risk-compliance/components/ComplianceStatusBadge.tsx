import type { ComplianceCheckStatus } from '../types/riskCompliance.types'

export function ComplianceStatusBadge({ status }: { status: ComplianceCheckStatus }) {
  const key = String(status || '').toUpperCase()
  const tone = key.includes('NON') || key.includes('OVERDUE') ? 'critical' : key.includes('COMPLIANT') ? 'success' : key.includes('WAIVED') ? 'warning' : 'neutral'
  return <span className={`badge ${tone}`}>{key || 'UNKNOWN'}</span>
}

export function OverdueIndicator({ dueAt, status }: { dueAt: string | null; status: string }) {
  if (!dueAt) return null
  const overdue = new Date(dueAt).getTime() < Date.now() && !['COMPLIANT', 'WAIVED'].includes(status)
  if (!overdue) return null
  return <span className="badge critical">Overdue</span>
}

export function EvidenceRequiredMarker({ required }: { required: boolean }) {
  return required ? <span className="badge warning">Evidence Required</span> : null
}
