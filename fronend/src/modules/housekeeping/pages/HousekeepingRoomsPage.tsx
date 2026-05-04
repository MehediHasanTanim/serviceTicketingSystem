import { useMemo, useState } from 'react'
import { useAuth } from '../../../features/auth/authContext'
import { RoomStatusModal } from '../components/RoomStatusModal'
import { useRoomStatuses, useUpdateRoomStatus } from '../hooks/useRoomStatuses'

export function HousekeepingRoomsPage() {
  const { auth } = useAuth()
  const [propertyId, setPropertyId] = useState('')
  const [search, setSearch] = useState('')
  const [selectedRoom, setSelectedRoom] = useState<number | null>(null)
  const { data, loading, error, reload } = useRoomStatuses(auth?.accessToken, propertyId ? Number(propertyId) : undefined)
  const { mutate, saving } = useUpdateRoomStatus(auth?.accessToken)

  const rows = useMemo(() => data.filter((r) => String(r.room_id).includes(search.trim())), [data, search])
  const room = rows.find((r) => r.room_id === selectedRoom) || null

  return (
    <div className="page full"><div className="glass panel"><div className="section-head"><h2>Housekeeping Rooms</h2><button className="button secondary small" onClick={reload}>Refresh</button></div>
      <div className="grid-form filters-grid"><input className="input" placeholder="Property ID" value={propertyId} onChange={(e) => setPropertyId(e.target.value)} /><input className="input" placeholder="Search room" value={search} onChange={(e) => setSearch(e.target.value)} /></div>
      {loading ? <p className="helper">Loading room statuses...</p> : null}
      {error ? <p className="error">{error}</p> : null}
      {!loading && !error ? <div className="cards-grid">{rows.map((r) => <article className="glass panel" key={r.id}><h3>Room {r.room_id}</h3><p>{r.occupancy_status}</p><p>{r.housekeeping_status}</p><p>{r.priority}</p><p>{new Date(r.updated_at).toLocaleString()}</p><button className="button small" onClick={() => setSelectedRoom(r.room_id)}>Update Status</button></article>)}</div> : null}
      <RoomStatusModal open={!!room} room={room} saving={saving} onClose={() => setSelectedRoom(null)} onSubmit={async (payload) => { await mutate(payload); await reload() }} />
    </div></div>
  )
}
