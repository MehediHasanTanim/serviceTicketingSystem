import type { ProjectStatus, SnagStatus, TechnicalAuditStatus } from '../types/projects.types'

export function priorityClass(priority: string) {
  return priority === 'CRITICAL' ? 'urgent' : priority.toLowerCase()
}

export function isProjectOverdue(plannedEndDate: string | null, status: ProjectStatus) {
  if (!plannedEndDate) return false
  if (['COMPLETED', 'CANCELLED', 'VOID'].includes(status)) return false
  return new Date(plannedEndDate).getTime() < Date.now()
}

export function allowedSnagActions(status: SnagStatus) {
  if (status === 'OPEN') return ['assign', 'start', 'cancel', 'void'] as const
  if (status === 'ASSIGNED') return ['assign', 'start', 'resolve', 'cancel', 'void'] as const
  if (status === 'IN_PROGRESS') return ['resolve', 'cancel', 'void'] as const
  if (status === 'RESOLVED') return ['verify', 'reopen'] as const
  if (status === 'REOPENED') return ['assign', 'start', 'void'] as const
  return [] as const
}

export function allowedAuditActions(status: TechnicalAuditStatus) {
  if (status === 'SCHEDULED') return ['start', 'cancel', 'void'] as const
  if (status === 'IN_PROGRESS') return ['complete', 'cancel', 'void'] as const
  return [] as const
}
