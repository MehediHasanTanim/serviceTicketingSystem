import type { ComplaintStatus } from '../types/guestComplaints.types'

export type LifecycleAction = 'assign' | 'start' | 'escalate' | 'resolve' | 'confirm' | 'reopen' | 'void'

const matrix: Record<ComplaintStatus, LifecycleAction[]> = {
  NEW: ['assign', 'void'],
  TRIAGED: ['assign', 'escalate', 'void'],
  ASSIGNED: ['start', 'escalate', 'resolve', 'void'],
  IN_PROGRESS: ['escalate', 'resolve', 'void'],
  ESCALATED: ['start', 'resolve', 'void'],
  RESOLVED: ['confirm', 'reopen'],
  CONFIRMED: [],
  REOPENED: ['assign', 'start', 'escalate', 'void'],
  CLOSED: [],
  VOID: [],
}

export function allowedActions(status: ComplaintStatus) {
  return matrix[status] || []
}

export function isOverdue(dueAt: string | null, status: string) {
  if (!dueAt) return false
  if (['RESOLVED', 'CONFIRMED', 'CLOSED', 'VOID'].includes(status)) return false
  return new Date(dueAt).getTime() < Date.now()
}
