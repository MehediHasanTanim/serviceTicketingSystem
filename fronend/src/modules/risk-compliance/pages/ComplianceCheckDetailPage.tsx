import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { ApprovalTrail } from '../components/ApprovalTrail'
import { EvidenceRequiredMarker } from '../components/ComplianceStatusBadge'
import { useApprovalTrail, useComplianceCheckDetail, useComplianceRequirementDetail, useDecideApprovalTrail, useSubmitComplianceCheck, useWaiveComplianceCheck } from '../hooks/useRiskCompliance'

export function ComplianceCheckDetailPage() {
  const { auth } = useAuth()
  const { id } = useParams()
  const checkId = Number(id)
  const { data: check, loading, error, reload } = useComplianceCheckDetail(auth?.accessToken, auth?.user?.org_id, checkId)
  const { data: requirement } = useComplianceRequirementDetail(auth?.accessToken, auth?.user?.org_id, check?.requirement_id)
  const { data: approvalTrail, reload: reloadTrail } = useApprovalTrail(auth?.accessToken, auth?.user?.org_id, 'compliance_check', String(checkId))
  const decideApprovalTrail = useDecideApprovalTrail()
  const submitCheck = useSubmitComplianceCheck()
  const waiveCheck = useWaiveComplianceCheck()
  const [compliant, setCompliant] = useState(true)
  const [evidenceAttachmentId, setEvidenceAttachmentId] = useState('')
  const [notes, setNotes] = useState('')
  const [waiveReason, setWaiveReason] = useState('')
  const [modal, setModal] = useState<'submit' | 'waive' | ''>('')
  const [actionError, setActionError] = useState('')

  const requiresEvidence = Boolean(requirement?.checklist_items?.some((item) => item.evidence_required))
  const canSubmit = !loading && !!check

  const onSubmit = async () => {
    if (!auth?.accessToken || !auth?.user?.org_id || !check) return
    setActionError('')
    if (requiresEvidence && !evidenceAttachmentId) {
      setActionError('Evidence is required for this checklist.')
      return
    }
    if (!compliant && !notes.trim()) {
      setActionError('Reason is required for non-compliant submission.')
      return
    }
    await submitCheck(auth.accessToken, check.id, { org_id: auth.user.org_id, compliant, evidence_attachment_id: evidenceAttachmentId ? Number(evidenceAttachmentId) : null, notes: notes.trim() })
    setModal('')
    await reload()
  }

  const onWaive = async () => {
    if (!auth?.accessToken || !auth?.user?.org_id || !check) return
    setActionError('')
    if (!waiveReason.trim()) {
      setActionError('Waive reason is required.')
      return
    }
    await waiveCheck(auth.accessToken, check.id, { org_id: auth.user.org_id, notes: waiveReason.trim() })
    setModal('')
    await reload()
  }

  if (loading) return <div className="page full"><div className="glass panel"><p>Loading compliance check...</p></div></div>
  if (error || !check) return <div className="page full"><div className="glass panel"><p className="error-text">{error || 'Check not found.'}</p></div></div>

  return <div className="page full"><div className="glass panel"><h2>Compliance Check #{check.id}</h2>
    <div className="card-section"><h3>Requirement Overview</h3><p><strong>Requirement:</strong> {check.requirement_id}</p><p><strong>Status:</strong> {check.status}</p><p><strong>Due:</strong> {check.due_at ? new Date(check.due_at).toLocaleString() : '-'}</p></div>
    <div className="card-section"><h3>Checklist Responses</h3>{(requirement?.checklist_items || []).map((item, idx) => <div key={item.id || idx} className="list-item"><strong>{item.title}</strong> <EvidenceRequiredMarker required={item.evidence_required} /><div className="muted">{item.description || 'No description'}</div></div>)}</div>
    <div className="card-section"><h3>Evidence & Notes</h3><label className="field">Evidence Attachment ID<input className="input" value={evidenceAttachmentId} onChange={(e) => setEvidenceAttachmentId(e.target.value)} /></label><label className="field">Notes<textarea className="input" rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} /></label></div>
    <div className="row-actions"><label className="field"><input type="checkbox" checked={compliant} onChange={(e) => setCompliant(e.target.checked)} /> Mark as compliant</label><button className="button" disabled={!canSubmit} onClick={() => setModal('submit')}>Submit</button><button className="button secondary" disabled={!canSubmit} onClick={() => setModal('waive')}>Waive</button></div>
    <ApprovalTrail
      entries={approvalTrail?.results || []}
      canManage={Boolean(auth?.user?.is_super_admin || auth?.user?.permissions?.includes('risk_compliance.approvals.manage'))}
      onApprove={() => void (async () => {
        if (!auth?.accessToken || !auth?.user?.org_id) return
        await decideApprovalTrail(auth.accessToken, { org_id: auth.user.org_id, entity_type: 'compliance_check', entity_id: String(check.id), decision: 'APPROVE', comment: 'Approved from check detail' })
        await reloadTrail()
      })()}
      onReject={() => void (async () => {
        if (!auth?.accessToken || !auth?.user?.org_id) return
        await decideApprovalTrail(auth.accessToken, { org_id: auth.user.org_id, entity_type: 'compliance_check', entity_id: String(check.id), decision: 'REJECT', comment: 'Rejected from check detail' })
        await reloadTrail()
      })()}
    />
    {modal === 'submit' ? <div className="card-section" role="dialog" aria-label="Submit confirmation"><p>Confirm submit compliance check?</p>{!compliant ? <p className="hint">Reason is required for non-compliant submissions.</p> : null}{actionError ? <p className="error-text">{actionError}</p> : null}<div className="row-actions"><button className="button" onClick={() => void onSubmit()}>Confirm</button><button className="button secondary" onClick={() => setModal('')}>Cancel</button></div></div> : null}
    {modal === 'waive' ? <div className="card-section" role="dialog" aria-label="Waive confirmation"><p>Confirm waive compliance check?</p><label className="field">Waive Reason<textarea className="input" rows={2} value={waiveReason} onChange={(e) => setWaiveReason(e.target.value)} /></label>{actionError ? <p className="error-text">{actionError}</p> : null}<div className="row-actions"><button className="button" onClick={() => void onWaive()}>Confirm</button><button className="button secondary" onClick={() => setModal('')}>Cancel</button></div></div> : null}
  </div></div>
}
