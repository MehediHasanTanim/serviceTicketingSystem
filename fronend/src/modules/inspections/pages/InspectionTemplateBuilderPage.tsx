import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { TemplateBuilder } from '../components/TemplateBuilder/TemplateBuilder'
import { useCreateInspectionTemplate, useInspectionTemplateDetail, useUpdateInspectionTemplate } from '../hooks/useInspections'
import type { InspectionChecklistSection } from '../types/inspections.types'

export function InspectionTemplateBuilderPage() {
  const { id } = useParams()
  const isEdit = useMemo(() => !!id, [id])
  const { auth } = useAuth()
  const navigate = useNavigate()
  const createTemplate = useCreateInspectionTemplate()
  const updateTemplate = useUpdateInspectionTemplate()
  const { data, loading } = useInspectionTemplateDetail(auth?.accessToken, auth?.user?.org_id, Number(id))
  const [form, setForm] = useState({ template_code: '', name: '', description: '', category: '', property_id: '', department_id: '', is_active: true })
  const [sections, setSections] = useState<InspectionChecklistSection[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    if (!data) return
    setForm({ template_code: data.template_code, name: data.name, description: data.description, category: data.category, property_id: data.property_id ? String(data.property_id) : '', department_id: data.department_id ? String(data.department_id) : '', is_active: data.is_active })
    setSections(data.sections || [])
  }, [data])

  const submit = async () => {
    if (!auth?.accessToken || !auth.user?.org_id) return
    setError('')
    if (!form.name.trim()) return setError('Name is required')
    if (!isEdit && !form.template_code.trim()) return setError('Template code is required')

    const payload: Record<string, unknown> = {
      org_id: auth.user.org_id,
      template_code: form.template_code,
      name: form.name,
      description: form.description,
      category: form.category,
      property_id: form.property_id ? Number(form.property_id) : null,
      department_id: form.department_id ? Number(form.department_id) : null,
      is_active: form.is_active,
      sections: sections.map((section, sectionIdx) => ({ ...section, sort_order: sectionIdx + 1, items: section.items.map((item, itemIdx) => ({ ...item, sort_order: itemIdx + 1 })) })),
    }

    if (isEdit && id) {
      await updateTemplate(auth.accessToken, Number(id), payload)
    } else {
      await createTemplate(auth.accessToken, payload)
    }
    navigate('/inspections/templates')
  }

  return <div className="page full"><div className="glass panel">
    <h2>{isEdit ? 'Edit' : 'New'} Inspection Template</h2>
    {loading ? <p>Loading...</p> : null}
    {error ? <p className="error-text">{error}</p> : null}
    <div className="grid-form three">
      <input className="input" placeholder="Template Code" disabled={isEdit} value={form.template_code} onChange={(e) => setForm((p) => ({ ...p, template_code: e.target.value }))} />
      <input className="input" placeholder="Name" value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))} />
      <input className="input" placeholder="Category" value={form.category} onChange={(e) => setForm((p) => ({ ...p, category: e.target.value }))} />
      <input className="input" placeholder="Property ID" value={form.property_id} onChange={(e) => setForm((p) => ({ ...p, property_id: e.target.value }))} />
      <input className="input" placeholder="Department ID" value={form.department_id} onChange={(e) => setForm((p) => ({ ...p, department_id: e.target.value }))} />
      <label><input type="checkbox" checked={form.is_active} onChange={(e) => setForm((p) => ({ ...p, is_active: e.target.checked }))} /> Active</label>
    </div>
    <textarea className="input" placeholder="Description" value={form.description} onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))} />
    <TemplateBuilder sections={sections} setSections={setSections} />
    <div className="inline-actions"><button className="button" onClick={submit}>Save</button><button className="button secondary" onClick={() => navigate('/inspections/templates')}>Cancel</button></div>
  </div></div>
}
