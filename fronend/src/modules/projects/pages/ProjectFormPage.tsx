import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { ProjectForm } from '../components/ProjectForm'
import { useCreateProject, useProjectDetail, useUpdateProject } from '../hooks/useProjects'

export function ProjectFormPage() {
  const { id } = useParams()
  const projectId = Number(id)
  const mode = projectId ? 'edit' : 'create'
  const { auth } = useAuth()
  const navigate = useNavigate()
  const detail = useProjectDetail(auth?.accessToken, auth?.user?.org_id, projectId)
  const create = useCreateProject()
  const update = useUpdateProject()
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')

  const onSubmit = async (payload: Record<string, unknown>) => {
    if (!auth?.accessToken || !auth.user?.org_id) return
    setSaving(true)
    setError('')
    try {
      if (mode === 'create') {
        const row = await create(auth.accessToken, payload)
        setToast('Project created successfully')
        setTimeout(() => navigate(`/projects/${row.id}`), 300)
      } else {
        await update(auth.accessToken, projectId, payload)
        setToast('Project updated successfully')
        setTimeout(() => navigate(`/projects/${projectId}`), 300)
      }
    } catch (err: any) {
      setError(err.message || 'Request failed')
    } finally {
      setSaving(false)
      setTimeout(() => setToast(''), 2200)
    }
  }

  if (mode === 'edit' && detail.loading) return <div className="page full"><div className="glass panel"><p>Loading project...</p></div></div>

  return <div className="page full"><div className="glass panel">
    <div className="section-head"><h2>{mode === 'create' ? 'Create Project' : 'Edit Project'}</h2></div>
    <ProjectForm orgId={auth?.user?.org_id || 0} mode={mode} initial={detail.data || undefined} saving={saving} apiError={error} onSubmit={onSubmit} />
    {toast ? <div className="toast">{toast}</div> : null}
  </div></div>
}
