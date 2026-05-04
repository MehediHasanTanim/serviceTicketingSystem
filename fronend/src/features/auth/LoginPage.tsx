import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from './authContext'
import { type ApiError } from '../../shared/api/client'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    org_id: 1,
    email: 'admin@example.com',
    password: 'Sansons1$',
  })
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
      const apiError = err as ApiError
      setError(apiError.details?.detail || apiError.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <div className="layout">
        <section className="glass hero">
          <span className="hero-badge">Operations Suite</span>
          <h1 className="hero-title">Service Ticketing System</h1>
          <p className="helper">
            Consolidate housekeeping, maintenance, and guest operations in one workspace.
          </p>
          <div className="hero-card">
            <strong>Live Ops Insights</strong>
            <p style={{ margin: '8px 0 0 0' }}>
              Track service orders, compliance checks, and team performance in real time.
            </p>
          </div>
        </section>
        <section className="glass panel">
          <form onSubmit={onSubmit}>
            <h2>Sign in</h2>
            <p className="helper">Use your organization credentials to continue.</p>
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
        </section>
      </div>
    </div>
  )
}
