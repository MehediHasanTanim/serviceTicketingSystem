import { useEffect, useState } from 'react'
import { corporateApi } from '../api/corporate.api'

function useAsyncState<T>(loader: () => Promise<T>, deps: Array<unknown>, enabled = true) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const reload = async () => {
    if (!enabled) return
    setLoading(true)
    setError('')
    try { setData(await loader()) } catch (e: any) { setError(e?.message || 'Request failed'); setData(null) } finally { setLoading(false) }
  }
  useEffect(() => { reload() }, deps)
  return { data, loading, error, reload }
}

export const useSuppliers = (token?: string, query?: Record<string, unknown>) => useAsyncState(() => corporateApi.getSuppliers(token || '', query || {}), [token, JSON.stringify(query)], !!token && !!query)
export const useSupplierDetail = (token?: string, id?: number, orgId?: number) => useAsyncState(() => corporateApi.getSupplier(token || '', id || 0, orgId || 0), [token, id, orgId], !!token && !!id && !!orgId)
export const useCreateSupplier = () => corporateApi.createSupplier
export const useUpdateSupplier = () => corporateApi.updateSupplier

export const useContracts = (token?: string, query?: Record<string, unknown>) => useAsyncState(() => corporateApi.getContracts(token || '', query || {}), [token, JSON.stringify(query)], !!token && !!query)
export const useContractDetail = (token?: string, id?: number, orgId?: number) => useAsyncState(() => corporateApi.getContract(token || '', id || 0, orgId || 0), [token, id, orgId], !!token && !!id && !!orgId)
export const useCreateContract = () => corporateApi.createContract
export const useUpdateContract = () => corporateApi.updateContract

export const usePurchaseOrders = (token?: string, query?: Record<string, unknown>) => useAsyncState(() => corporateApi.getPurchaseOrders(token || '', query || {}), [token, JSON.stringify(query)], !!token && !!query)
export const usePurchaseOrderDetail = (token?: string, id?: number, orgId?: number) => useAsyncState(() => corporateApi.getPurchaseOrder(token || '', id || 0, orgId || 0), [token, id, orgId], !!token && !!id && !!orgId)
export const useCreatePurchaseOrder = () => corporateApi.createPurchaseOrder
export const useUpdatePurchaseOrder = () => corporateApi.updatePurchaseOrder
export const usePurchaseOrderAction = () => corporateApi.poAction

export const useCapexRequests = (token?: string, query?: Record<string, unknown>) => useAsyncState(() => corporateApi.getCapexRequests(token || '', query || {}), [token, JSON.stringify(query)], !!token && !!query)
export const useCapexRequestDetail = (token?: string, id?: number, orgId?: number) => useAsyncState(() => corporateApi.getCapexRequest(token || '', id || 0, orgId || 0), [token, id, orgId], !!token && !!id && !!orgId)
export const useCreateCapexRequest = () => corporateApi.createCapexRequest
export const useUpdateCapexRequest = () => corporateApi.updateCapexRequest
export const useCapexAction = () => corporateApi.capexAction

export const useApprovalQueue = (token?: string, query?: Record<string, unknown>) => useAsyncState(() => corporateApi.getApprovalQueue(token || '', query || {}), [token, JSON.stringify(query)], !!token && !!query)
export const useApprovalDecision = () => corporateApi.approvalDecision

export const useCorporateAuditLogs = (token?: string, query?: Record<string, unknown>) => useAsyncState(() => corporateApi.getCorporateAuditLogs(token || '', query || {}), [token, JSON.stringify(query)], !!token && !!query)
