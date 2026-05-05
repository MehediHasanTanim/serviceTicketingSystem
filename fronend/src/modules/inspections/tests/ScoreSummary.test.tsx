import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ScoreSummary } from '../components/Scoring/ScoreSummary'

describe('ScoreSummary', () => {
  it('renders final score and result', () => {
    render(<ScoreSummary finalScore="88.4" result="FAIL" />)
    expect(screen.getByText(/88.40/)).toBeInTheDocument()
    expect(screen.getByText(/FAIL/)).toBeInTheDocument()
  })

  it('handles all NA state', () => {
    render(<ScoreSummary finalScore="0" result="NOT_APPLICABLE" />)
    expect(screen.getByText(/Not applicable/)).toBeInTheDocument()
  })
})
