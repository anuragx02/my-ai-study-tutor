import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { to: '/', label: 'Dashboard' },
  { to: '/courses', label: 'Courses' },
  { to: '/materials', label: 'Study Materials' },
  { to: '/chat', label: 'AI Chat Tutor' },
  { to: '/quiz', label: 'Quiz Interface' },
  { to: '/analytics', label: 'Analytics' },
  { to: '/recommendations', label: 'Recommendations' },
  { to: '/admin', label: 'Admin Panel', roles: ['admin'] },
]

export default function Layout() {
  const { user, logout } = useAuth()

  const filteredNavItems = navItems.filter((item) => {
    if (item.roles && user) {
      return item.roles.includes(user.role)
    }
    return true
  })

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <h1>AI Study Tutor</h1>
          <span className="muted">Learn, quiz, and improve</span>
          <span className="muted">{user?.name} · {user?.role}</span>
        </div>
        <nav className="nav-list">
          {filteredNavItems.map((item) => (
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
