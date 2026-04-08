import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function PublicRoute() {
  const { user, authReady } = useAuth()

  if (!authReady) {
    return <section className="card" style={{ margin: '20vh auto', maxWidth: 420 }}>Loading session...</section>
  }

  if (user) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}