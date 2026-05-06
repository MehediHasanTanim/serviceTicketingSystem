import { useEffect, useState } from 'react'
import {
  createProject,
  createSnaggingItem,
  createTechnicalAudit,
  fetchProjectAuditLogs,
  fetchProjectDetail,
  fetchProjectSnaggingItems,
  fetchProjectTimeline,
  fetchProjects,
  fetchSnaggingItemDetail,
  fetchTechnicalAuditDetail,
  fetchTechnicalAudits,
  snaggingItemAction,
  technicalAuditAction,
  updateProject,
  updateProjectProgress,
  updateProjectStatus,
  updateSnaggingItem,
  updateTechnicalAudit,
} from '../api/projects.api'
import type { ProjectAuditLogFilters, ProjectListFilters, SnaggingListFilters, TechnicalAuditListFilters } from '../types/projects.types'

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
      setError(err.message || 'Request failed')
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { reload() }, deps)
  return { data, loading, error, reload }
}

export function useProjects(accessToken?: string, orgId?: number, filters?: ProjectListFilters) {
  return useAsyncState(() => fetchProjects(accessToken || '', orgId || 0, filters || { q: '', property: '', department: '', project_type: '', status: '', priority: '', owner: '', manager: '', date_from: '', date_to: '', page: 1, page_size: 10, sort_by: 'updated_at', sort_dir: 'desc' }), [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId && !!filters)
}
export function useProjectDetail(accessToken?: string, orgId?: number, id?: number) {
  return useAsyncState(() => fetchProjectDetail(accessToken || '', orgId || 0, id || 0), [accessToken, orgId, id], !!accessToken && !!orgId && !!id)
}
export function useProjectTimeline(accessToken?: string, orgId?: number, projectId?: number) {
  return useAsyncState(() => fetchProjectTimeline(accessToken || '', orgId || 0, projectId || 0), [accessToken, orgId, projectId], !!accessToken && !!orgId && !!projectId)
}
export function useProjectSnaggingItems(accessToken?: string, orgId?: number, projectId?: number, filters?: SnaggingListFilters) {
  return useAsyncState(() => fetchProjectSnaggingItems(accessToken || '', orgId || 0, projectId || 0, filters || { q: '', category: '', severity: '', status: '', assigned_to: '', room: '', location: '', due_from: '', due_to: '', page: 1, page_size: 10, sort_by: 'created_at', sort_dir: 'desc' }), [accessToken, orgId, projectId, JSON.stringify(filters)], !!accessToken && !!orgId && !!projectId && !!filters)
}
export function useSnaggingItemDetail(accessToken?: string, orgId?: number, snagId?: number) {
  return useAsyncState(() => fetchSnaggingItemDetail(accessToken || '', orgId || 0, snagId || 0), [accessToken, orgId, snagId], !!accessToken && !!orgId && !!snagId)
}
export function useTechnicalAudits(accessToken?: string, orgId?: number, projectId?: number, filters?: TechnicalAuditListFilters) {
  return useAsyncState(() => fetchTechnicalAudits(accessToken || '', orgId || 0, projectId || 0, filters || { q: '', status: '', result: '', auditor: '', conducted_from: '', conducted_to: '', page: 1, page_size: 10, sort_by: 'created_at', sort_dir: 'desc' }), [accessToken, orgId, projectId, JSON.stringify(filters)], !!accessToken && !!orgId && !!projectId && !!filters)
}
export function useTechnicalAuditDetail(accessToken?: string, orgId?: number, auditId?: number) {
  return useAsyncState(() => fetchTechnicalAuditDetail(accessToken || '', orgId || 0, auditId || 0), [accessToken, orgId, auditId], !!accessToken && !!orgId && !!auditId)
}
export function useProjectAuditLogs(accessToken?: string, orgId?: number, filters?: ProjectAuditLogFilters) {
  return useAsyncState(() => fetchProjectAuditLogs(accessToken || '', orgId || 0, filters || { q: '', property_id: '', actor_user_id: '', action: '', target_type: '', target_id: '', date_from: '', date_to: '', page: 1, page_size: 10, sort_by: 'created_at', sort_dir: 'desc' }), [accessToken, orgId, JSON.stringify(filters)], !!accessToken && !!orgId && !!filters)
}

export const useCreateProject = () => createProject
export const useUpdateProject = () => updateProject
export const useUpdateProjectStatus = () => updateProjectStatus
export const useUpdateProjectProgress = () => updateProjectProgress
export const useCreateSnaggingItem = () => createSnaggingItem
export const useUpdateSnaggingItem = () => updateSnaggingItem
export const useSnaggingItemAction = () => snaggingItemAction
export const useCreateTechnicalAudit = () => createTechnicalAudit
export const useUpdateTechnicalAudit = () => updateTechnicalAudit
export const useTechnicalAuditAction = () => technicalAuditAction
