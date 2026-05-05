import { useEffect, useState } from 'react'
import {
  assignComplaint,
  completeComplaintFollowUp,
  complaintLifecycleAction,
  confirmComplaintResolution,
  createComplaintFollowUp,
  createGuestComplaint,
  escalateComplaint,
  getComplaintAnalyticsResolutionTime,
  getComplaintAnalyticsSatisfaction,
  getComplaintAnalyticsSummary,
  getComplaintAnalyticsTrends,
  getComplaintAuditLogs,
  getComplaintFollowUps,
  getGuestComplaint,
  getGuestComplaints,
  updateGuestComplaint,
} from '../api/guestComplaints.api'
import type { ComplaintListFilters } from '../types/guestComplaints.types'

function useAsyncState<T>(loader: () => Promise<T>, deps: Array<unknown>, enabled = true) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const reload = async () => {
    if (!enabled) return
    setLoading(true)
    setError('')
    try {
      setData(await loader())
    } catch (err: any) {
      setData(null)
      setError(err.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { reload() }, deps)
  return { data, loading, error, reload }
}

export function useGuestComplaints(accessToken?: string, orgId?: number, filters?: ComplaintListFilters) {
  return useAsyncState(() => getGuestComplaints(accessToken || '', orgId || 0, filters || { q: '', status: '', severity: '', category: '', source: '', property: '', department: '', assigned_to: '', escalated_to: '', date_from: '', date_to: '', page: 1, page_size: 10 }), [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId && !!filters)
}
export function useGuestComplaintDetail(accessToken?: string, orgId?: number, complaintId?: number) {
  return useAsyncState(() => getGuestComplaint(accessToken || '', orgId || 0, complaintId || 0), [accessToken, orgId, complaintId], !!accessToken && !!orgId && !!complaintId)
}
export function useComplaintFollowUps(accessToken?: string, orgId?: number, complaintId?: number) {
  return useAsyncState(() => getComplaintFollowUps(accessToken || '', orgId || 0, complaintId || 0), [accessToken, orgId, complaintId], !!accessToken && !!orgId && !!complaintId)
}

export function useComplaintAlerts(accessToken?: string, orgId?: number, filters?: ComplaintListFilters) {
  return useAsyncState(async () => {
    const token = accessToken || ''
    const org = orgId || 0
    const rows = await getGuestComplaints(token, org, filters || { q: '', status: '', severity: '', category: '', source: '', property: '', department: '', assigned_to: '', escalated_to: '', date_from: '', date_to: '', page: 1, page_size: 50 })
    const audit = await getComplaintAuditLogs(token, org, {})
    const now = Date.now()
    const escalatedIds = new Set(audit.results.filter((x) => x.action.includes('escalated')).map((x) => Number(x.entity_id)))
    const reopenedIds = new Set(audit.results.filter((x) => x.action.includes('reopened')).map((x) => Number(x.entity_id)))
    const followUpsByComplaint = await Promise.all(rows.results.map(async (complaint) => ({ complaintId: complaint.id, followUps: (await getComplaintFollowUps(token, org, complaint.id)).results })))
    const missedMap = new Map<number, boolean>()
    followUpsByComplaint.forEach((x) => missedMap.set(x.complaintId, x.followUps.some((f) => f.status === 'MISSED')))

    return rows.results.flatMap((complaint) => {
      const reasons: Array<'CRITICAL' | 'OVERDUE' | 'ESCALATED' | 'REOPENED' | 'LOW_SATISFACTION' | 'FOLLOW_UP_MISSED'> = []
      if (complaint.severity === 'CRITICAL') reasons.push('CRITICAL')
      if (complaint.due_at && new Date(complaint.due_at).getTime() < now && !['CLOSED', 'VOID', 'RESOLVED', 'CONFIRMED'].includes(complaint.status)) reasons.push('OVERDUE')
      if (complaint.status === 'ESCALATED' || escalatedIds.has(complaint.id)) reasons.push('ESCALATED')
      if (complaint.status === 'REOPENED' || reopenedIds.has(complaint.id)) reasons.push('REOPENED')
      if (complaint.satisfaction_score && Number(complaint.satisfaction_score) <= 2) reasons.push('LOW_SATISFACTION')
      if (missedMap.get(complaint.id)) reasons.push('FOLLOW_UP_MISSED')
      return reasons.map((reason) => ({ complaint, reason, triggered_at: complaint.updated_at }))
    })
  }, [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId)
}

export function useGuestComplaintAnalytics(accessToken?: string, orgId?: number, filters?: Record<string, string>) {
  return useAsyncState(async () => {
    const [summary, trends, resolution, satisfaction] = await Promise.all([
      getComplaintAnalyticsSummary(accessToken || '', orgId || 0, filters || {}),
      getComplaintAnalyticsTrends(accessToken || '', orgId || 0, filters || {}),
      getComplaintAnalyticsResolutionTime(accessToken || '', orgId || 0, filters || {}),
      getComplaintAnalyticsSatisfaction(accessToken || '', orgId || 0, filters || {}),
    ])
    return { summary, trends, resolution, satisfaction }
  }, [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId)
}

export function useComplaintAuditLog(accessToken?: string, orgId?: number, filters?: { action?: string; target_id?: string }) {
  return useAsyncState(() => getComplaintAuditLogs(accessToken || '', orgId || 0, filters || {}), [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId)
}

export const useCreateGuestComplaint = () => createGuestComplaint
export const useUpdateGuestComplaint = () => updateGuestComplaint
export const useComplaintLifecycleAction = () => complaintLifecycleAction
export const useAssignComplaint = () => assignComplaint
export const useEscalateComplaint = () => escalateComplaint
export const useCreateFollowUp = () => createComplaintFollowUp
export const useCompleteFollowUp = () => completeComplaintFollowUp
export const useConfirmResolution = () => confirmComplaintResolution
