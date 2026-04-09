import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      await register(form)
      navigate('/', { replace: true })
    } catch (submitError) {
      const response = submitError.response?.data
      setError(response?.detail || Object.values(response || {})[0]?.[0] || 'Unable to register.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="card" style={{ maxWidth: 640, margin: '7vh auto' }}>
      <h2 className="page-title">Register</h2>
      <p className="muted">Create your student account.</p>
      <form onSubmit={handleSubmit} className="feature-grid" style={{ marginTop: 20 }}>
        <input className="input" placeholder="Full name" value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} />
        <input className="input" placeholder="Email" type="email" value={form.email} onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))} />
        <input className="input" placeholder="Password" type="password" value={form.password} onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))} />
        {error ? <div style={{ color: '#ff8b92', gridColumn: '1 / -1' }}>{error}</div> : null}
        <button className="button" style={{ marginTop: 20, gridColumn: '1 / -1' }} type="submit" disabled={loading}>
          {loading ? 'Creating account...' : 'Create account'}
        </button>
      </form>
      <p className="muted" style={{ marginTop: 16 }}>
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </section>
  )
}
