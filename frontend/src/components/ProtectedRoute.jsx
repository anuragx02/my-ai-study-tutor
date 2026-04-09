import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute() {
  const { user, authReady } = useAuth()
  const location = useLocation()

  if (!authReady) {
    return <section className="card" style={{ margin: '20vh auto', maxWidth: 420 }}>Loading session...</section>
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return <Outlet />
}