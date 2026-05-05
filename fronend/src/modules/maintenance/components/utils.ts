export function toIsoOrNull(input: string) {
  return input ? new Date(input).toISOString() : null
}

export function decimal(value: string | number) {
  const num = typeof value === 'number' ? value : Number(value || 0)
  if (!Number.isFinite(num)) return '0.00'
  return num.toFixed(2)
}

export function sumMoney(values: Array<string | number>) {
  const total = values.reduce<number>((acc, curr) => acc + (Number(curr) || 0), 0)
  return decimal(total)
}

export function getAllowedActions(status: string) {
  if (status === 'OPEN') return ['assign', 'start', 'cancel', 'void']
  if (status === 'ASSIGNED') return ['assign', 'start', 'cancel', 'void']
  if (status === 'IN_PROGRESS') return ['hold', 'complete', 'cancel', 'void']
  if (status === 'ON_HOLD') return ['start', 'cancel', 'void']
  return []
}
