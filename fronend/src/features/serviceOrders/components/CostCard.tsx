import { useMemo, useState } from 'react'
import { formatCurrency, isValidNonNegativeNumber } from '../utils'

type Props = {
  partsCost: string
  laborCost: string
  compensationCost: string
  busy?: boolean
  onSave: (values: { parts_cost: string; labor_cost: string; compensation_cost: string }) => Promise<void> | void
}

export function CostCard({ partsCost, laborCost, compensationCost, busy, onSave }: Props) {
  const [parts, setParts] = useState(partsCost)
  const [labor, setLabor] = useState(laborCost)
  const [compensation, setCompensation] = useState(compensationCost)
  const [error, setError] = useState('')

  const total = useMemo(() => {
    const p = Number(parts || 0)
    const l = Number(labor || 0)
    const c = Number(compensation || 0)
    return p + l + c
  }, [parts, labor, compensation])

  const dirty = parts !== partsCost || labor !== laborCost || compensation !== compensationCost

  const save = async () => {
    if (![parts, labor, compensation].every(isValidNonNegativeNumber)) {
      setError('All values must be non-negative numbers.')
      return
    }
    setError('')
    await onSave({ parts_cost: parts, labor_cost: labor, compensation_cost: compensation })
  }

  return (
    <div className="card-section">
      <h4>Costs</h4>
      <div className="grid-form three">
        <label className="field">Parts cost<input className="input" value={parts} onChange={(e) => setParts(e.target.value)} aria-label="Parts cost" /></label>
        <label className="field">Labor cost<input className="input" value={labor} onChange={(e) => setLabor(e.target.value)} aria-label="Labor cost" /></label>
        <label className="field">Compensation cost<input className="input" value={compensation} onChange={(e) => setCompensation(e.target.value)} aria-label="Compensation cost" /></label>
      </div>
      <p><strong>Total:</strong> {formatCurrency(total)}</p>
      {error ? <p className="error-text">{error}</p> : null}
      <button className="button small" disabled={busy || !dirty} onClick={save}>Save Costs</button>
    </div>
  )
}
