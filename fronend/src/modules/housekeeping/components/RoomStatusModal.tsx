import { useMemo, useState } from 'react'
import type { RoomStatusRow } from '../types/housekeeping.types'

const occupancyOptions = ['OCCUPIED', 'VACANT', 'RESERVED', 'OUT_OF_ORDER'] as const
const hkOptions = ['CLEAN', 'DIRTY', 'INSPECTING', 'READY', 'BLOCKED'] as const

function validTransitions(current: RoomStatusRow['housekeeping_status']) {
  const map: Record<string, string[]> = {
    CLEAN: ['DIRTY', 'INSPECTING', 'BLOCKED'],
    DIRTY: ['CLEAN', 'INSPECTING', 'BLOCKED'],
    INSPECTING: ['READY', 'DIRTY', 'BLOCKED'],
    READY: ['CLEAN', 'DIRTY', 'BLOCKED'],
    BLOCKED: ['DIRTY', 'CLEAN'],
  }
  return map[current] || hkOptions
}

export function RoomStatusModal({ room, open, saving, onClose, onSubmit }: {
  room: RoomStatusRow | null
  open: boolean
  saving?: boolean
  onClose: () => void
  onSubmit: (payload: Record<string, unknown>) => Promise<void> | void
}) {
  const [occupancy, setOccupancy] = useState<RoomStatusRow['occupancy_status']>('VACANT')
  const [housekeeping, setHousekeeping] = useState<RoomStatusRow['housekeeping_status']>('DIRTY')
  const [priority, setPriority] = useState<'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT'>('MEDIUM')
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')

  const options = useMemo(() => (room ? validTransitions(room.housekeeping_status) : hkOptions), [room])
  if (!open || !room) return null

  const requiresReason = housekeeping === 'BLOCKED' || occupancy === 'OUT_OF_ORDER'
  const critical = housekeeping === 'BLOCKED' || occupancy === 'OUT_OF_ORDER'

  const handleSubmit = async () => {
    if (requiresReason && !reason.trim()) {
      setError('Reason is required for blocked or out-of-order updates.')
      return
    }
    if (critical && !window.confirm('This is a critical status change. Continue?')) return
    await onSubmit({ room_id: room.room_id, occupancy_status: occupancy, housekeeping_status: housekeeping, priority, reason: reason.trim() || undefined })
    onClose()
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <div className="modal" role="dialog" aria-modal="true" aria-label="Room status update">
        <h3>Room Status Update</h3>
        <p>Current: {room.occupancy_status} / {room.housekeeping_status}</p>
        <label className="field">Occupancy<select className="input" value={occupancy} onChange={(e) => setOccupancy(e.target.value as any)}>{occupancyOptions.map((o) => <option key={o} value={o}>{o}</option>)}</select></label>
        <label className="field">Housekeeping<select className="input" value={housekeeping} onChange={(e) => setHousekeeping(e.target.value as any)}>{options.map((o) => <option key={o} value={o}>{o}</option>)}</select></label>
        <label className="field">Priority<select className="input" value={priority} onChange={(e) => setPriority(e.target.value as any)}><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>URGENT</option></select></label>
        <label className="field">Reason<textarea className="input" rows={3} value={reason} onChange={(e) => setReason(e.target.value)} /></label>
        {error ? <p className="error">{error}</p> : null}
        <div className="modal-actions"><button className="button secondary small" onClick={onClose}>Cancel</button><button className="button small" disabled={saving} onClick={handleSubmit}>Update</button></div>
      </div>
    </div>
  )
}
