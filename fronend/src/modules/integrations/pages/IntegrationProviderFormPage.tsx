import { type FormEvent, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../../../features/auth/authContext'
import { useCreateIntegrationProvider, useIntegrationProviderDetail, useUpdateIntegrationProvider } from '../hooks/useIntegrations'

const defaultForm = { provider_code: '', name: '', provider_type: 'PMS', status: 'ACTIVE', base_url: '', auth_type: 'NONE', credentials_secret_ref: '', timeout_seconds: '30', retry_policy: '{"max_retries":3}', config: '{}' }

export function IntegrationProviderFormPage() {
  const { auth } = useAuth()
  const { id } = useParams()
  const editId = id ? Number(id) : 0
  const isEdit = Boolean(editId)
  const navigate = useNavigate()
  const create = useCreateIntegrationProvider()
  const update = useUpdateIntegrationProvider()
  const { data } = useIntegrationProviderDetail(auth?.accessToken, editId)
  const [form, setForm] = useState(defaultForm)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!data) return
    setForm((prev) => ({ ...prev, provider_code: data.provider_code || '', name: data.name || '', provider_type: data.provider_type || 'PMS', status: data.status || 'ACTIVE', base_url: data.base_url || '', auth_type: data.auth_type || 'NONE', credentials_secret_ref: data.credentials_secret_ref ? '***masked***' : '', timeout_seconds: String(data.timeout_seconds || 30), retry_policy: JSON.stringify(data.retry_policy || { max_retries: 3 }, null, 2), config: JSON.stringify(data.config || {}, null, 2) }))
  }, [data])

  const validate = () => {
    if (!form.provider_code.trim()) return 'provider_code is required'
    if (!form.name.trim()) return 'name is required'
    if (!form.provider_type.trim()) return 'provider_type is required'
    if (!form.base_url.trim()) return 'base_url is required for API-based integrations'
    if (Number(form.timeout_seconds) <= 0) return 'timeout_seconds must be positive'
    try { JSON.parse(form.retry_policy || '{}') } catch { return 'retry_policy must be valid JSON' }
    try { JSON.parse(form.config || '{}') } catch { return 'config must be valid JSON' }
    if (form.base_url && !/^https?:\/\//.test(form.base_url)) return 'base_url must be a valid http(s) URL'
    return ''
  }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!auth?.accessToken || !auth.user?.org_id) return
    const v = validate()
    if (v) { setError(v); return }
    setSaving(true)
    setError('')
    const payload = { org_id: auth.user.org_id, provider_code: form.provider_code.trim(), name: form.name.trim(), provider_type: form.provider_type, status: form.status, base_url: form.base_url.trim(), auth_type: form.auth_type, credentials_secret_ref: form.credentials_secret_ref === '***masked***' ? undefined : form.credentials_secret_ref.trim(), timeout_seconds: Number(form.timeout_seconds), retry_policy: JSON.parse(form.retry_policy || '{}'), config: JSON.parse(form.config || '{}') }
    try {
      if (isEdit) await update(auth.accessToken, editId, payload)
      else await create(auth.accessToken, payload)
      navigate('/integrations/providers')
    } catch (err: any) {
      setError(err?.details?.detail || err?.message || 'Failed to save provider')
    } finally { setSaving(false) }
  }

  return <div className='page full'><div className='glass panel'><h2>{isEdit ? 'Edit Integration Provider' : 'New Integration Provider'}</h2>
    <form className='card-section' onSubmit={onSubmit}><div className='grid-form two'>
      <label className='field'>Provider Code<input className='input' value={form.provider_code} onChange={(e) => setForm({ ...form, provider_code: e.target.value })} required /></label>
      <label className='field'>Name<input className='input' value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></label>
      <label className='field'>Type<select className='input' value={form.provider_type} onChange={(e) => setForm({ ...form, provider_type: e.target.value })}><option value='PMS'>PMS</option><option value='ACCOUNTING'>ACCOUNTING</option><option value='BAS_IOT'>BAS_IOT</option><option value='EMAIL'>EMAIL</option><option value='SMS'>SMS</option><option value='OTHER'>OTHER</option></select></label>
      <label className='field'>Status<select className='input' value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}><option value='ACTIVE'>ACTIVE</option><option value='INACTIVE'>INACTIVE</option><option value='ERROR'>ERROR</option><option value='ARCHIVED'>ARCHIVED</option></select></label>
      <label className='field'>Base URL<input className='input' value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value })} /></label>
      <label className='field'>Auth Type<select className='input' value={form.auth_type} onChange={(e) => setForm({ ...form, auth_type: e.target.value })}><option value='NONE'>NONE</option><option value='API_KEY'>API_KEY</option><option value='BASIC'>BASIC</option><option value='BEARER_TOKEN'>BEARER_TOKEN</option><option value='OAUTH2'>OAUTH2</option><option value='CUSTOM'>CUSTOM</option></select></label>
      <label className='field'>Credentials Secret Ref<input aria-label='Credentials Secret Ref' className='input' value={form.credentials_secret_ref} onChange={(e) => setForm({ ...form, credentials_secret_ref: e.target.value })} /></label>
      <label className='field'>Timeout Seconds<input aria-label='Timeout Seconds' type='number' min={1} className='input' value={form.timeout_seconds} onChange={(e) => setForm({ ...form, timeout_seconds: e.target.value })} /></label>
    </div>
    <label className='field'>Retry Policy JSON<textarea aria-label='Retry Policy JSON' className='input' rows={5} value={form.retry_policy} onChange={(e) => setForm({ ...form, retry_policy: e.target.value })} /></label>
    <label className='field'>Config JSON<textarea aria-label='Config JSON' className='input' rows={7} value={form.config} onChange={(e) => setForm({ ...form, config: e.target.value })} /></label>
    {error ? <p className='error-text'>{error}</p> : null}
    <div className='row-actions'><button className='button' type='submit' disabled={saving}>{saving ? 'Saving...' : (isEdit ? 'Update Provider' : 'Create Provider')}</button></div>
    </form>
  </div></div>
}
