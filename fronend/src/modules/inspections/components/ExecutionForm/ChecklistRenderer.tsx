import type { InspectionChecklistSection, InspectionResponseValue } from '../../types/inspections.types'

type ResponseState = Record<number, { response: InspectionResponseValue | ''; comment: string; evidence_attachment_id: string }>

type Props = {
  sections: InspectionChecklistSection[]
  responses: ResponseState
  setResponses: (next: ResponseState) => void
  readOnly: boolean
}

export function ChecklistRenderer({ sections, responses, setResponses, readOnly }: Props) {
  const setItem = (itemId: number, key: 'response' | 'comment' | 'evidence_attachment_id', value: string) => {
    setResponses({ ...responses, [itemId]: { ...responses[itemId], response: responses[itemId]?.response || '', comment: responses[itemId]?.comment || '', evidence_attachment_id: responses[itemId]?.evidence_attachment_id || '', [key]: value } })
  }

  return <div>
    {sections.sort((a, b) => a.sort_order - b.sort_order).map((section) => <div key={section.id || section.sort_order} className="card-section">
      <h3>{section.title}</h3>
      <p className="hint">{section.description || 'No description'}</p>
      {section.items.sort((a, b) => a.sort_order - b.sort_order).map((item) => {
        const state = responses[item.id || -1] || { response: '', comment: '', evidence_attachment_id: '' }
        const showEvidence = state.response === 'FAIL' && item.non_compliance_trigger
        const failNeedsComment = state.response === 'FAIL' && !state.comment.trim()
        return <div key={item.id || item.sort_order} className="card-section" data-testid={`check-item-${item.id || item.sort_order}`}>
          <div><strong>{item.question}</strong> {item.is_required ? <span aria-label="required">*</span> : null} {item.non_compliance_trigger ? <span className="pill">NCR</span> : null}</div>
          <p className="hint">{item.description || 'No description'}</p>
          <div className="inline-actions">
            {(['PASS', 'FAIL', 'NA'] as const).map((option) => <label key={option}><input disabled={readOnly} type="radio" name={`resp-${item.id}`} checked={state.response === option} onChange={() => setItem(item.id || -1, 'response', option)} /> {option}</label>)}
          </div>
          <input disabled={readOnly} className="input" placeholder="Comment" value={state.comment} onChange={(e) => setItem(item.id || -1, 'comment', e.target.value)} />
          {showEvidence ? <input disabled={readOnly} className="input" placeholder="Evidence Attachment ID" value={state.evidence_attachment_id} onChange={(e) => setItem(item.id || -1, 'evidence_attachment_id', e.target.value)} /> : null}
          {failNeedsComment ? <p className="error-text">FAIL requires comment.</p> : null}
        </div>
      })}
    </div>)}
  </div>
}
