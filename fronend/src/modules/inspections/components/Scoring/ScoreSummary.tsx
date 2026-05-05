import type { InspectionRunResult } from '../../types/inspections.types'

export function ScoreSummary({ finalScore, result }: { finalScore: string | number; result: InspectionRunResult }) {
  const numeric = Number(finalScore || 0)
  if (result === 'NOT_APPLICABLE') {
    return <div className="card-section"><h3>Score Summary</h3><p className="hint">Not applicable: all responses are N/A.</p></div>
  }
  return <div className="card-section" data-testid="score-summary"><h3>Score Summary</h3><p>Final score: <strong>{numeric.toFixed(2)}%</strong></p><p>Result: <strong>{result || 'N/A'}</strong></p></div>
}
