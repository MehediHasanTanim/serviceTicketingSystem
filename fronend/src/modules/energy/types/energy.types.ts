export type Pagination<T> = { count: number; page?: number; page_size?: number; results: T[] }

export type Grouping = 'day' | 'week' | 'month' | 'quarter' | 'year'
export type MetricType = 'ELECTRICITY' | 'GAS' | 'WATER' | 'STEAM' | 'CHILLED_WATER' | 'DIESEL' | 'WASTE' | 'CARBON_EMISSIONS' | 'OTHER'
export type UtilityType = 'ELECTRICITY' | 'GAS' | 'WATER' | 'DIESEL' | 'WASTE' | 'OTHER'
export type ReadingSource = 'MANUAL' | 'CSV_IMPORT' | 'IOT_METER' | 'UTILITY_BILL' | 'API_INTEGRATION'

export type EnergyAnalyticsFilter = {
  org_id: number
  property_id?: string
  department_id?: string
  metric_type?: string
  utility_type?: string
  source?: string
  grouping?: Grouping
  date_from?: string
  date_to?: string
}

export type EnergySummary = {
  total_energy_usage?: number | string
  total_water_usage?: number | string
  total_carbon_emissions?: number | string
  total_utility_cost?: number | string
}

export type EnergyTrendPoint = { period: string; total: number | string }
export type EnergyTrends = {
  grouping: Grouping
  results: EnergyTrendPoint[]
  month_over_month_change?: number | string | null
  year_over_year_change?: number | string | null
  peak_usage_period?: { period?: string | null; total?: number | string }
}

export type EnergyEfficiency = {
  average_energy_per_room_night?: number | string
  average_water_per_room_night?: number | string
  average_cost_per_room_night?: number | string
  energy_per_sqft?: number | string
  carbon_per_room_night?: number | string
}

export type EnergyCosts = {
  total_utility_cost?: number | string
  highest_cost_utility_type?: string | null
}

export type SustainabilityProgress = {
  target_id: number
  computed_status: 'ACTIVE' | 'ACHIEVED' | 'MISSED' | 'ARCHIVED'
  actual_value?: number | string
  progress_pct?: number | string
  target_value?: number | string
  metric_type?: string
}
export type SustainabilityAnalytics = { targets: SustainabilityProgress[] }

export type EnergyKPIReading = {
  id: number
  org_id: number
  property_id: number
  department_id?: number | null
  meter_id?: number | null
  source: ReadingSource
  reading_date: string
  period_start: string
  period_end: string
  metric_type: MetricType
  raw_value: string
  raw_unit: string
  normalized_value: string
  normalized_unit: string
  occupancy_count?: number | null
  room_nights?: number | null
  covers_count?: number | null
  area_sqft?: string | null
  external_reference_id?: string | null
  metadata?: Record<string, unknown>
  ingested_by?: number | null
  created_at: string
}

export type UtilityCostStatus = 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'PAID' | 'VOID'
export type UtilityCost = {
  id: number
  org_id: number
  property_id: number
  department_id?: number | null
  vendor_id?: number | null
  utility_type: UtilityType
  billing_period_start: string
  billing_period_end: string
  usage_value: string
  usage_unit: string
  base_charge: string
  variable_charge: string
  tax_amount: string
  adjustment_amount: string
  total_cost: string
  currency: string
  invoice_number?: string
  status: UtilityCostStatus
  updated_at: string
}

export type SustainabilityTargetStatus = 'ACTIVE' | 'ACHIEVED' | 'MISSED' | 'ARCHIVED'
export type SustainabilityTarget = {
  id: number
  org_id: number
  property_id: number
  metric_type: MetricType
  target_period: 'DAY' | 'WEEK' | 'MONTH' | 'QUARTER' | 'YEAR'
  target_value: string
  target_unit: string
  normalized_target_value: string
  normalized_target_unit: string
  start_date: string
  end_date: string
  status: SustainabilityTargetStatus
}

export type EnergyAuditLog = {
  id: number
  created_at: string
  actor_user_id?: number | null
  action: string
  target_type: string
  target_id: string
  metadata?: Record<string, unknown>
  property_id?: number | null
}
