import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import PublicRoute from './components/PublicRoute'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import ChatTutorPage from './pages/ChatTutorPage'
import KnowledgeBasePage from './pages/KnowledgeBasePage'
import QuizPage from './pages/QuizPage'
import InsightsPage from './pages/InsightsPage'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<PublicRoute />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/materials" element={<KnowledgeBasePage />} />
            <Route path="/chat" element={<ChatTutorPage />} />
            <Route path="/quiz" element={<QuizPage />} />
            <Route path="/insights" element={<InsightsPage />} />
            <Route path="/analytics" element={<Navigate to="/insights" replace />} />
            <Route path="/recommendations" element={<Navigate to="/insights" replace />} />
            <Route path="/courses" element={<Navigate to="/materials" replace />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}
