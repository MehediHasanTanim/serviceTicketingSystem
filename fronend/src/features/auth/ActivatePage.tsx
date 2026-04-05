import { useMemo, useState, type FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { apiRequest } from '../../shared/api/client'

export function ActivatePage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = useMemo(() => searchParams.get('token') || '', [searchParams])

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setSuccess('')

    if (!token) {
      setError('Activation token is missing.')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)
    try {
      await apiRequest('/auth/activate', {
        method: 'POST',
        body: JSON.stringify({ token, password }),
      })
      setSuccess('Account activated. Redirecting...')
      setTimeout(() => navigate('/activate/success'), 800)
    } catch (err: any) {
      const detail = err.details?.detail || err.message || 'Activation failed.'
      if (detail.toLowerCase().includes('expired')) {
        setError('This invite link has expired. Please request a new invite from your admin.')
      } else if (detail.toLowerCase().includes('already used')) {
        setError('This invite link was already used. Please sign in or request a new invite.')
      } else {
        setError(detail)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <div className="card">
        <h2>Activate Account</h2>
        <p className="helper">Set your password to activate your account.</p>
        <form className="form" onSubmit={onSubmit}>
          <label>
            New Password
            <input
              type="password"
              className="input"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Create a strong password"
              required
            />
          </label>
          <label>
            Confirm Password
            <input
              type="password"
              className="input"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              placeholder="Re-enter your password"
              required
            />
          </label>
          {error && <p className="error">{error}</p>}
          {success && <p className="success">{success}</p>}
          <button className="button" disabled={loading}>
            {loading ? 'Activating...' : 'Activate Account'}
          </button>
        </form>
      </div>
    </div>
  )
}
