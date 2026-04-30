import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import useStudyTimeTracker from '../hooks/useStudyTimeTracker'

const navItems = [
  { to: '/', label: 'Dashboard' },
  { to: '/chat', label: 'AI Chat Tutor' },
  { to: '/quiz', label: 'Quiz' },
  { to: '/insights', label: 'Insights' },
]

export default function Layout() {
  const { user, logout } = useAuth()
  useStudyTimeTracker(user)

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <h1>AI Study Tutor</h1>
          <span className="muted">Learn, quiz, and improve</span>
        </div>
        <nav className="nav-list nav-list--horizontal">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="topbar-actions">
          <span className="muted">{user?.name}</span>
          <button className="button" onClick={logout} type="button">
            Logout
          </button>
        </div>
      </header>
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}
