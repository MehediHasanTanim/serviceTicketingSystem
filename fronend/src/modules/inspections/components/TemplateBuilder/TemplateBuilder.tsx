import { useMemo } from 'react'
import type { InspectionChecklistSection } from '../../types/inspections.types'

type Props = {
  sections: InspectionChecklistSection[]
  setSections: (next: InspectionChecklistSection[]) => void
}

const baseItem = () => ({ question: '', description: '', response_type: 'PASS_FAIL_NA' as const, is_required: false, weight: '0', sort_order: 0, non_compliance_trigger: false })

export function TemplateBuilder({ sections, setSections }: Props) {
  const totalWeight = useMemo(() => sections.reduce((sum, section) => sum + Number(section.weight || 0), 0), [sections])

  const addSection = () => setSections([...sections, { title: '', description: '', sort_order: sections.length + 1, weight: '0', items: [] }])
  const updateSection = (idx: number, key: keyof InspectionChecklistSection, value: any) => {
    const next = sections.map((section, i) => (i === idx ? { ...section, [key]: value } : section))
    setSections(next)
  }

  const removeSection = (idx: number) => {
    if (sections[idx].items.length > 0 && !window.confirm('This section has checklist items. Delete anyway?')) return
    const next = sections.filter((_, i) => i !== idx).map((section, i) => ({ ...section, sort_order: i + 1 }))
    setSections(next)
  }

  const moveSection = (idx: number, dir: -1 | 1) => {
    const target = idx + dir
    if (target < 0 || target >= sections.length) return
    const next = [...sections]
    ;[next[idx], next[target]] = [next[target], next[idx]]
    setSections(next.map((section, i) => ({ ...section, sort_order: i + 1 })))
  }

  const addItem = (sectionIdx: number) => {
    const next = [...sections]
    next[sectionIdx].items = [...next[sectionIdx].items, { ...baseItem(), sort_order: next[sectionIdx].items.length + 1 }]
    setSections(next)
  }

  const updateItem = (sectionIdx: number, itemIdx: number, key: string, value: any) => {
    const next = [...sections]
    next[sectionIdx].items = next[sectionIdx].items.map((item, i) => (i === itemIdx ? { ...item, [key]: value } : item))
    setSections(next)
  }

  const removeItem = (sectionIdx: number, itemIdx: number) => {
    const next = [...sections]
    next[sectionIdx].items = next[sectionIdx].items.filter((_, i) => i !== itemIdx).map((item, i) => ({ ...item, sort_order: i + 1 }))
    setSections(next)
  }

  const moveItem = (sectionIdx: number, itemIdx: number, dir: -1 | 1) => {
    const items = [...sections[sectionIdx].items]
    const target = itemIdx + dir
    if (target < 0 || target >= items.length) return
    ;[items[itemIdx], items[target]] = [items[target], items[itemIdx]]
    const next = [...sections]
    next[sectionIdx].items = items.map((item, i) => ({ ...item, sort_order: i + 1 }))
    setSections(next)
  }

  return <div className="card-section">
    <div className="section-head"><h3>Checklist Sections</h3><button className="button secondary small" onClick={addSection}>Add Section</button></div>
    <p className="hint">Total section weight: {totalWeight.toFixed(2)}</p>
    {sections.map((section, sectionIdx) => <div key={sectionIdx} className="card-section" data-testid={`section-${sectionIdx}`}>
      <div className="section-head"><strong>Section {sectionIdx + 1}</strong><div className="inline-actions"><button className="button secondary small" onClick={() => moveSection(sectionIdx, -1)}>Up</button><button className="button secondary small" onClick={() => moveSection(sectionIdx, 1)}>Down</button><button className="button secondary small" onClick={() => removeSection(sectionIdx)}>Delete</button></div></div>
      <div className="grid-form three">
        <input aria-label="Section title" className="input" placeholder="Title" value={section.title} onChange={(e) => updateSection(sectionIdx, 'title', e.target.value)} />
        <input aria-label="Section description" className="input" placeholder="Description" value={section.description} onChange={(e) => updateSection(sectionIdx, 'description', e.target.value)} />
        <input aria-label="Section weight" className="input" type="number" min={0} value={section.weight} onChange={(e) => updateSection(sectionIdx, 'weight', Math.max(0, Number(e.target.value)).toString())} />
      </div>
      <div className="section-head"><strong>Items</strong><button className="button secondary small" onClick={() => addItem(sectionIdx)}>Add Item</button></div>
      {section.items.map((item, itemIdx) => <div key={itemIdx} className="grid-form three" data-testid={`item-${sectionIdx}-${itemIdx}`}>
        <input aria-label="Question" className="input" value={item.question} placeholder="Question" onChange={(e) => updateItem(sectionIdx, itemIdx, 'question', e.target.value)} />
        <input aria-label="Item description" className="input" value={item.description} placeholder="Description" onChange={(e) => updateItem(sectionIdx, itemIdx, 'description', e.target.value)} />
        <input aria-label="Item weight" className="input" type="number" min={0} value={item.weight} onChange={(e) => updateItem(sectionIdx, itemIdx, 'weight', Math.max(0, Number(e.target.value)).toString())} />
        <label><input type="checkbox" checked={item.is_required} onChange={(e) => updateItem(sectionIdx, itemIdx, 'is_required', e.target.checked)} /> Required</label>
        <label><input type="checkbox" checked={item.non_compliance_trigger} onChange={(e) => updateItem(sectionIdx, itemIdx, 'non_compliance_trigger', e.target.checked)} /> Non-compliance trigger</label>
        <div className="inline-actions"><button className="button secondary small" onClick={() => moveItem(sectionIdx, itemIdx, -1)}>Up</button><button className="button secondary small" onClick={() => moveItem(sectionIdx, itemIdx, 1)}>Down</button><button className="button secondary small" onClick={() => removeItem(sectionIdx, itemIdx)}>Delete</button></div>
      </div>)}
    </div>)}
  </div>
}
