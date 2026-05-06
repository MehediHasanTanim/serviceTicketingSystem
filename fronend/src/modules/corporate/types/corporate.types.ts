export type PaginatedResponse<T> = { count: number; results: T[] }

export type SupplierStatus = 'ACTIVE' | 'INACTIVE' | 'BLACKLISTED' | 'ARCHIVED'
export type ContractStatus = 'DRAFT' | 'ACTIVE' | 'EXPIRED' | 'TERMINATED' | 'RENEWAL_DUE' | 'ARCHIVED'
export type POStatus = 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'ORDERED' | 'PARTIALLY_RECEIVED' | 'RECEIVED' | 'CANCELLED' | 'VOID'
export type CAPEXStatus = 'DRAFT' | 'SUBMITTED' | 'UNDER_REVIEW' | 'APPROVED' | 'REJECTED' | 'BUDGET_RELEASED' | 'COMPLETED' | 'CANCELLED' | 'VOID'

export type Supplier = {
  id: number
  org_id: number
  supplier_code: string
  name: string
  contact_person: string
  email: string
  phone: string
  address: string
  tax_id: string
  category: string
  status: SupplierStatus
  rating: number | null
  notes: string
  created_at: string
  updated_at: string
}

export type Contract = {
  id: number
  org_id: number
  contract_code: string
  supplier_id: number
  title: string
  description: string
  contract_type: string
  status: ContractStatus
  effective_date: string
  expiry_date: string
  renewal_due_at: string | null
  contract_value: string
  currency: string
  attachment_id: number | null
  owner_id: number | null
  created_at: string
  updated_at: string
}

export type POLineItem = {
  id?: number
  item_name: string
  description: string
  quantity: string
  unit_price: string
  tax_rate: string
  discount_amount: string
  line_total?: string
}

export type PurchaseOrder = {
  id: number
  org_id: number
  po_number: string
  supplier_id: number
  contract_id: number | null
  property_id: number | null
  department_id: number | null
  requester_id: number
  approver_id: number | null
  secondary_approver_id: number | null
  status: POStatus
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT'
  requested_date: string | null
  required_by: string | null
  approved_at: string | null
  ordered_at: string | null
  received_at: string | null
  subtotal: string
  tax_amount: string
  discount_amount: string
  total_amount: string
  currency: string
  notes: string
  line_items: POLineItem[]
}

export type CAPEXRequest = {
  id: number
  org_id: number
  capex_number: string
  title: string
  description: string
  property_id: number | null
  department_id: number | null
  requester_id: number
  approver_id: number | null
  secondary_approver_id: number | null
  category: string
  status: CAPEXStatus
  estimated_amount: string
  approved_amount: string
  currency: string
  justification: string
  business_impact: string
  requested_at: string | null
  approved_at: string | null
  completed_at: string | null
}

export type ApprovalRecord = {
  id: number
  org_id: number
  entity_type: 'PURCHASE_ORDER' | 'CAPEX_REQUEST'
  entity_id: number
  approval_level: number
  approver_id: number
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'SKIPPED' | 'CANCELLED'
  decision_comment: string
  decided_at: string | null
  created_at: string
}

export type AuditLog = {
  id: number
  org_id: number
  actor_user_id: number | null
  action: string
  target_type: string
  target_id: string
  metadata: Record<string, unknown>
  created_at: string
}
