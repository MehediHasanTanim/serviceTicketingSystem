import type { IntegrationJobStatus, IntegrationStatus } from '../types/integrations.types'

const SENSITIVE_KEYS = ['password', 'token', 'secret', 'authorization', 'api_key', 'apikey', 'key']

export function maskSensitive(input: unknown): unknown {
  if (Array.isArray(input)) return input.map(maskSensitive)
  if (!input || typeof input !== 'object') return input
  const out: Record<string, unknown> = {}
  Object.entries(input as Record<string, unknown>).forEach(([k, v]) => {
    out[k] = SENSITIVE_KEYS.some((x) => k.toLowerCase().includes(x)) ? '***MASKED***' : maskSensitive(v)
  })
  return out
}

export function SafeJson({ value }: { value: unknown }) {
  const parsed = typeof value === 'string' ? (() => { try { return JSON.parse(value) } catch { return value } })() : value
  return <pre>{JSON.stringify(maskSensitive(parsed ?? {}), null, 2)}</pre>
}

export function StatusBadge({ status }: { status?: string }) {
  const s = (status || '').toUpperCase() as IntegrationStatus | IntegrationJobStatus
  const cls = s === 'ACTIVE' || s === 'SUCCESS' ? 'ok' : s === 'ERROR' || s === 'FAILED' || s === 'DEAD_LETTER' ? 'err' : 'warn'
  return <span className={`status-chip ${cls}`}>{s || '-'}</span>
}

export function NumberSafe({ value, suffix = '' }: { value: unknown; suffix?: string }) {
  const n = Number(value)
  return <>{Number.isFinite(n) ? `${n}${suffix}` : `0${suffix}`}</>
}
