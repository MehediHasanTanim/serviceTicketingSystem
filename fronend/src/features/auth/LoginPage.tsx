import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from './authContext'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ org_id: 1, email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const onChange = (key: 'org_id' | 'email' | 'password') => (event: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [key]: event.target.value }))
  }

  const onSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login({
        org_id: Number(form.org_id),
        email: form.email.trim(),
        password: form.password,
      })
      navigate('/home')
    } catch (err) {
      setError(err.details?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell" style={{ padding: '48px' }}>
      <div style={{ display: 'grid', alignContent: 'center', gap: '20px' }}>
        <h1>Service Ticketing System</h1>
        <p className="helper">
          Log in to access your operational dashboard.
        </p>
      </div>
      <div style={{ display: 'grid', alignContent: 'center' }}>
        <form className="panel" onSubmit={onSubmit}>
          <h2>Sign in</h2>
          <label>
            Organization ID
            <input
              className="input"
              type="number"
              min="1"
              value={form.org_id}
              onChange={onChange('org_id')}
              required
            />
          </label>
          <label style={{ marginTop: '16px', display: 'block' }}>
            Email
            <input
              className="input"
              type="email"
              value={form.email}
              onChange={onChange('email')}
              required
            />
          </label>
          <label style={{ marginTop: '16px', display: 'block' }}>
            Password
            <input
              className="input"
              type="password"
              value={form.password}
              onChange={onChange('password')}
              required
            />
          </label>
          {error && <p className="error" style={{ marginTop: '12px' }}>{error}</p>}
          <button className="button" style={{ marginTop: '24px' }} disabled={loading}>
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
