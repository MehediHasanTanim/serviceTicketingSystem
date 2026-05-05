import { useEffect, useState } from 'react'
import {
  acknowledgeRiskComplianceAlert,
  activateComplianceRequirement,
  completeMitigation,
  decideApprovalTrail,
  createAuditRecord,
  createComplianceRequirement,
  createLegalRecord,
  createMitigation,
  createRisk,
  deactivateComplianceRequirement,
  fetchAuditRecordDetail,
  fetchAuditRecords,
  fetchComplianceCheckDetail,
  fetchComplianceChecks,
  fetchComplianceRequirementDetail,
  fetchComplianceRequirements,
  fetchLegalRecordDetail,
  fetchLegalRecords,
  fetchRiskComplianceAlerts,
  fetchRiskComplianceAuditLogs,
  fetchRiskComplianceDashboardLegalExpiry,
  fetchRiskComplianceDashboardRiskSummary,
  fetchRiskComplianceDashboardStatus,
  fetchRiskComplianceDashboardSummary,
  fetchRiskDetail,
  fetchRiskMitigations,
  fetchRiskRegistry,
  fetchApprovalTrail,
  resolveRiskComplianceAlert,
  submitComplianceCheck,
  updateComplianceRequirement,
  updateLegalRecord,
  updateRisk,
  waiveComplianceCheck,
} from '../api/riskCompliance.api'
import type {
  ComplianceCheckFilters,
  ComplianceRequirementFilters,
  LegalRecordFilters,
  RiskComplianceAuditLogFilters,
  RiskFilters,
} from '../types/riskCompliance.types'

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
      setError(err?.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { reload() }, deps)
  return { data, loading, error, reload }
}

export function useComplianceRequirements(accessToken?: string, orgId?: number, filters?: ComplianceRequirementFilters) {
  return useAsyncState(() => fetchComplianceRequirements(accessToken || '', orgId || 0, filters || { q: '', category: '', property: '', department: '', owner: '', priority: '', status: '', page: 1, page_size: 10 }), [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId && !!filters)
}

export function useComplianceRequirementDetail(accessToken?: string, orgId?: number, id?: number) {
  return useAsyncState(() => fetchComplianceRequirementDetail(accessToken || '', orgId || 0, id || 0), [accessToken, orgId, id], !!accessToken && !!orgId && !!id)
}

export function useComplianceChecks(accessToken?: string, orgId?: number, filters?: ComplianceCheckFilters) {
  return useAsyncState(() => fetchComplianceChecks(accessToken || '', orgId || 0, filters || { requirement_id: '', status: '', property: '', department: '', owner: '', assigned_to: '', priority: '', category: '', page: 1, page_size: 10 }), [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId && !!filters)
}

export function useComplianceCheckDetail(accessToken?: string, orgId?: number, id?: number) {
  return useAsyncState(() => fetchComplianceCheckDetail(accessToken || '', orgId || 0, id || 0), [accessToken, orgId, id], !!accessToken && !!orgId && !!id)
}

export function useRiskRegistry(accessToken?: string, orgId?: number, filters?: RiskFilters) {
  return useAsyncState(() => fetchRiskRegistry(accessToken || '', orgId || 0, filters || { q: '', risk_level: '', status: '', category: '', property: '', department: '', owner: '', due_from: '', due_to: '', page: 1, page_size: 10 }), [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId && !!filters)
}

export function useRiskDetail(accessToken?: string, orgId?: number, id?: number) {
  return useAsyncState(async () => {
    const [risk, mitigations] = await Promise.all([
      fetchRiskDetail(accessToken || '', orgId || 0, id || 0),
      fetchRiskMitigations(accessToken || '', orgId || 0, id || 0),
    ])
    return { risk, mitigations: mitigations.results }
  }, [accessToken, orgId, id], !!accessToken && !!orgId && !!id)
}

export function useLegalRecords(accessToken?: string, orgId?: number, filters?: LegalRecordFilters) {
  return useAsyncState(() => fetchLegalRecords(accessToken || '', orgId || 0, filters || { q: '', type: '', status: '', property: '', department: '', owner: '', expiry_from: '', expiry_to: '', page: 1, page_size: 10 }), [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId && !!filters)
}

export function useLegalRecordDetail(accessToken?: string, orgId?: number, id?: number) {
  return useAsyncState(() => fetchLegalRecordDetail(accessToken || '', orgId || 0, id || 0), [accessToken, orgId, id], !!accessToken && !!orgId && !!id)
}

export function useAuditRecords(accessToken?: string, orgId?: number) {
  return useAsyncState(() => fetchAuditRecords(accessToken || '', orgId || 0), [accessToken, orgId], !!accessToken && !!orgId)
}

export function useAuditRecordDetail(accessToken?: string, orgId?: number, id?: number) {
  return useAsyncState(() => fetchAuditRecordDetail(accessToken || '', orgId || 0, id || 0), [accessToken, orgId, id], !!accessToken && !!orgId && !!id)
}

export function useRiskComplianceDashboard(accessToken?: string, orgId?: number, withinDays = 30) {
  return useAsyncState(async () => {
    const [summary, complianceStatus, riskSummary, legalExpiry] = await Promise.all([
      fetchRiskComplianceDashboardSummary(accessToken || '', orgId || 0),
      fetchRiskComplianceDashboardStatus(accessToken || '', orgId || 0),
      fetchRiskComplianceDashboardRiskSummary(accessToken || '', orgId || 0),
      fetchRiskComplianceDashboardLegalExpiry(accessToken || '', orgId || 0, withinDays),
    ])
    return { summary, complianceStatus, riskSummary, legalExpiry }
  }, [accessToken, orgId, withinDays], !!accessToken && !!orgId)
}

export function useRiskComplianceAlerts(accessToken?: string, orgId?: number) {
  return useAsyncState(() => fetchRiskComplianceAlerts(accessToken || '', orgId || 0), [accessToken, orgId], !!accessToken && !!orgId)
}

export function useRiskComplianceAuditLogs(accessToken?: string, orgId?: number, filters?: RiskComplianceAuditLogFilters) {
  return useAsyncState(() => fetchRiskComplianceAuditLogs(accessToken || '', orgId || 0, filters || { q: '', actor_user_id: '', action: '', target_type: '', target_id: '', date_from: '', date_to: '', requirement: '', risk: '', legal_record: '', audit_record: '', page: 1, page_size: 20, sort_by: 'created_at', sort_dir: 'desc' }), [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId && !!filters)
}

export function useApprovalTrail(accessToken?: string, orgId?: number, entityType?: string, entityId?: string | number) {
  return useAsyncState(() => fetchApprovalTrail(accessToken || '', orgId || 0, entityType || '', entityId || ''), [accessToken, orgId, entityType, entityId], !!accessToken && !!orgId && !!entityType && !!entityId)
}

export const useCreateComplianceRequirement = () => createComplianceRequirement
export const useUpdateComplianceRequirement = () => updateComplianceRequirement
export const useActivateComplianceRequirement = () => activateComplianceRequirement
export const useDeactivateComplianceRequirement = () => deactivateComplianceRequirement
export const useSubmitComplianceCheck = () => submitComplianceCheck
export const useWaiveComplianceCheck = () => waiveComplianceCheck
export const useCreateRisk = () => createRisk
export const useUpdateRisk = () => updateRisk
export const useCreateMitigation = () => createMitigation
export const useCompleteMitigation = () => completeMitigation
export const useCreateLegalRecord = () => createLegalRecord
export const useUpdateLegalRecord = () => updateLegalRecord
export const useCreateAuditRecord = () => createAuditRecord
export const useAcknowledgeRiskComplianceAlert = () => acknowledgeRiskComplianceAlert
export const useResolveRiskComplianceAlert = () => resolveRiskComplianceAlert
export const useDecideApprovalTrail = () => decideApprovalTrail
