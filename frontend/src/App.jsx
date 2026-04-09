import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import PublicRoute from './components/PublicRoute'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import ChatTutorPage from './pages/ChatTutorPage'
import CoursesPage from './pages/CoursesPage'
import MaterialsPage from './pages/MaterialsPage'
import QuizPage from './pages/QuizPage'
import AnalyticsPage from './pages/AnalyticsPage'
import RecommendationsPage from './pages/RecommendationsPage'

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
            <Route path="/courses" element={<CoursesPage />} />
            <Route path="/materials" element={<MaterialsPage />} />
            <Route path="/chat" element={<ChatTutorPage />} />
            <Route path="/quiz" element={<QuizPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/recommendations" element={<RecommendationsPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}
