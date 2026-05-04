import type { ServiceOrderStatus, TimelineItem } from './types'

export const STATUS_ACTIONS: Record<ServiceOrderStatus, Array<'assign' | 'start' | 'hold' | 'complete' | 'defer' | 'void' | 'reassign'>> = {
  OPEN: ['assign', 'void'],
  ASSIGNED: ['start', 'defer', 'void'],
  IN_PROGRESS: ['hold', 'complete', 'defer', 'void'],
  ON_HOLD: ['start', 'defer', 'void'],
  DEFERRED: ['reassign', 'void'],
  COMPLETED: [],
  VOID: [],
}

export function getAllowedActions(status: ServiceOrderStatus) {
  return STATUS_ACTIONS[status] || []
}

export function formatCurrency(value: string | number) {
  const num = typeof value === 'number' ? value : Number(value || 0)
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number.isFinite(num) ? num : 0)
}

export function toTimelineOrder(items: TimelineItem[]) {
  return [...items].sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime())
}

export function isValidNonNegativeNumber(raw: string) {
  if (raw.trim() === '') return false
  const num = Number(raw)
  return Number.isFinite(num) && num >= 0
}
