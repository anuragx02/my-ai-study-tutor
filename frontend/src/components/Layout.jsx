import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { to: '/', label: 'Dashboard', icon: 'DB' },
  { to: '/materials', label: 'Study Material', icon: 'SM' },
  { to: '/chat', label: 'AI Chat Tutor', icon: 'AI' },
  { to: '/quiz', label: 'Quiz', icon: 'QZ' },
  { to: '/insights', label: 'Insights', icon: 'IN' },
]

export default function Layout() {
  const { user, logout } = useAuth()

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
              <span className="nav-link__icon" aria-hidden="true">{item.icon}</span>
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
