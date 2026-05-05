import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { ChecklistRenderer } from '../components/ExecutionForm/ChecklistRenderer'
import { ScoreSummary } from '../components/Scoring/ScoreSummary'
import { useCompleteInspectionRun, useInspectionRunDetail, useInspectionTemplateDetail, useSubmitInspectionResponse } from '../hooks/useInspections'
import type { InspectionResponseValue } from '../types/inspections.types'

export function InspectionExecutionPage() {
  const { id } = useParams()
  const { auth } = useAuth()
  const runDetail = useInspectionRunDetail(auth?.accessToken, auth?.user?.org_id, Number(id))
  const templateDetail = useInspectionTemplateDetail(auth?.accessToken, auth?.user?.org_id, runDetail.data?.run.template_id)
  const submitResponse = useSubmitInspectionResponse()
  const completeRun = useCompleteInspectionRun()
  const [responses, setResponses] = useState<Record<number, { response: InspectionResponseValue | ''; comment: string; evidence_attachment_id: string }>>({})
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const raw = localStorage.getItem(`inspection-exec-${id}`)
    if (!raw) return
    try { setResponses(JSON.parse(raw)) } catch { }
  }, [id])

  useEffect(() => {
    localStorage.setItem(`inspection-exec-${id}`, JSON.stringify(responses))
  }, [id, responses])

  const readOnly = useMemo(() => ['COMPLETED', 'CANCELLED', 'VOID'].includes(runDetail.data?.run.status || ''), [runDetail.data?.run.status])

  const saveAll = async () => {
    if (!auth?.accessToken || !auth.user?.org_id || !runDetail.data) return
    setSaving(true)
    setError('')
    try {
      for (const [itemId, value] of Object.entries(responses)) {
        if (!value.response) continue
        await submitResponse(auth.accessToken, runDetail.data.run.id, { org_id: auth.user.org_id, checklist_item_id: Number(itemId), response: value.response, comment: value.comment, evidence_attachment_id: value.evidence_attachment_id ? Number(value.evidence_attachment_id) : null })
      }
      runDetail.reload()
    } catch (err: any) {
      setError(err.message || 'Failed to save responses')
    } finally {
      setSaving(false)
    }
  }

  const complete = async () => {
    if (!auth?.accessToken || !auth.user?.org_id || !runDetail.data) return
    if (!window.confirm('Complete this inspection run?')) return
    await saveAll()
    await completeRun(auth.accessToken, runDetail.data.run.id, { org_id: auth.user.org_id })
    runDetail.reload()
  }

  return <div className="page full"><div className="glass panel"><h2>Execute Inspection</h2>
    {runDetail.loading || templateDetail.loading ? <p>Loading...</p> : null}
    {runDetail.error || templateDetail.error || error ? <p className="error-text">{runDetail.error || templateDetail.error || error}</p> : null}
    {runDetail.data ? <div className="sticky-summary"><ScoreSummary finalScore={runDetail.data.run.final_score} result={runDetail.data.run.result} /></div> : null}
    {templateDetail.data ? <ChecklistRenderer sections={templateDetail.data.sections} responses={responses} setResponses={setResponses} readOnly={readOnly} /> : null}
    <div className="inline-actions"><button className="button" disabled={readOnly || saving} onClick={saveAll}>Save Responses</button><button className="button secondary" disabled={readOnly || saving} onClick={complete}>Complete Inspection</button></div>
  </div></div>
}
