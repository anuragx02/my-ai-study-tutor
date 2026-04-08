import { useAuth } from '../context/AuthContext'
import { Link } from 'react-router-dom'

export default function AdminPage() {
  const { user } = useAuth()

  if (user?.role !== 'admin') {
    return (
      <section className="card">
        <h2 className="page-title">Admin Panel</h2>
        <p className="muted">You do not have access to this area.</p>
        <Link className="button" to="/">Back to dashboard</Link>
      </section>
    )
  }

  return (
    <section className="card">
      <h2 className="page-title">Admin Panel</h2>
      <p className="muted">Admin scaffold.</p>
      <div className="card" style={{ marginTop: 20 }}>
        <strong>Current role</strong>
        <div className="muted">{user?.role || 'unknown'}</div>
      </div>
      <p className="muted" style={{ marginTop: 16 }}>
        Use the Courses and Study Materials pages to create content as an admin or tutor.
      </p>
    </section>
  )
}
