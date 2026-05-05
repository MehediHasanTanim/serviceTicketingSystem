import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { createTaskFromQR, lookupAssetByQR } from '../api/maintenance.api'

export function QRScanPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const [qrCode, setQrCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<Awaited<ReturnType<typeof lookupAssetByQR>> | null>(null)

  const lookup = async () => {
    if (!auth?.accessToken || !auth.user?.org_id || !qrCode.trim()) return
    setLoading(true)
    setError('')
    try {
      setResult(await lookupAssetByQR(auth.accessToken, auth.user.org_id, qrCode.trim()))
    } catch (err: any) {
      setError(err.message || 'Asset not found')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  const createTask = async () => {
    if (!auth?.accessToken || !auth.user?.org_id) return
    const title = prompt('Task title') || ''
    if (!title) return
    const created = await createTaskFromQR(auth.accessToken, qrCode.trim(), { org_id: auth.user.org_id, task_type: 'CORRECTIVE', title, description: '', priority: 'MEDIUM', housekeeping_status: 'DIRTY', timestamp: new Date().toISOString() })
    navigate(`/maintenance/orders/new?asset_id=${created.asset_id || ''}`)
  }

  return <div className="page full"><div className="glass panel"><h2>QR Scan Entry</h2><p className="hint">Camera integration can be added using browser media APIs. Manual QR input fallback is available now.</p><div className="grid-form two"><input className="input" placeholder="Enter QR code" value={qrCode} onChange={(e) => setQrCode(e.target.value)} /><button className="button" onClick={lookup}>Lookup</button></div>{loading ? <p>Looking up...</p> : null}{error ? <p className="error-text">{error}</p> : null}
    {result ? <div className="card-section"><h3>{result.asset.name}</h3><p>Code: {result.asset.asset_code} | Status: {result.current_status}</p><h4>Open tasks</h4><ul className="simple-list">{result.open_maintenance_tasks.map((task) => <li key={task.id}>{task.task_number} • {task.title}</li>)}</ul><h4>Recent logbook</h4><ul className="simple-list">{result.recent_logbook_entries.map((entry) => <li key={entry.id}>{entry.entry_type} • {entry.description}</li>)}</ul><button className="button" onClick={createTask}>Create Corrective Task</button></div> : null}
  </div></div>
}
