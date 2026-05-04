import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { TimelineView } from '../components/TimelineView'

describe('TimelineView', () => {
  it('renders timeline entries in reverse chronological order', () => {
    render(
      <TimelineView
        entries={[
          { id: '1', kind: 'created', actor: 'A', at: '2026-04-01T00:00:00Z', summary: 'Created' },
          { id: '2', kind: 'updated', actor: 'B', at: '2026-04-03T00:00:00Z', summary: 'Updated' },
          { id: '3', kind: 'remark', actor: 'C', at: '2026-04-02T00:00:00Z', summary: 'Remark' },
        ]}
      />,
    )

    const rows = screen.getAllByRole('listitem')
    expect(rows[0]).toHaveTextContent('Updated')
    expect(rows[1]).toHaveTextContent('Remark')
    expect(rows[2]).toHaveTextContent('Created')
  })
})
