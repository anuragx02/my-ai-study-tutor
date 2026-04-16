import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { to: '/', label: 'Dashboard' },
  { to: '/materials', label: 'Study Material' },
  { to: '/chat', label: 'AI Chat Tutor' },
  { to: '/quiz', label: 'Quiz' },
  { to: '/insights', label: 'Insights' },
]

export default function Layout() {
  const { user, logout } = useAuth()

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <h1>AI Study Tutor</h1>
          <span className="muted">Learn, quiz, and improve</span>
          <span className="muted">{user?.name}</span>
        </div>
        <nav className="nav-list">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <button className="button" style={{ marginTop: 20, width: '100%' }} onClick={logout} type="button">
          Logout
        </button>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}
