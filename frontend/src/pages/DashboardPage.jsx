import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import ProgressChart from '../components/ProgressChart'
import RecommendationCard from '../components/RecommendationCard'
import api from '../services/api'
import { getStoredOpenStudyMinutes } from '../utils/studyTime'

export default function DashboardPage() {
  const { user } = useAuth()
  const [summary, setSummary] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [openStudyMinutes, setOpenStudyMinutes] = useState(0)

  useEffect(() => {
    let active = true

    async function loadDashboard() {
      try {
        const [progressResponse, recommendationsResponse] = await Promise.all([
          api.get('/analytics/progress'),
          api.get('/recommendations/'),
        ])
        if (active) {
          setSummary(progressResponse.data)
          setRecommendations(recommendationsResponse.data)
        }
      } catch {
        if (active) {
          setSummary({ quiz_score_trend: [], accuracy: 0, weak_topics: [], study_time_minutes: 0 })
        }
      }
    }

    loadDashboard()
    return () => {
      active = false
    }
  }, [user?.id, user?.email])

  useEffect(() => {
    function refreshOpenStudyMinutes() {
      setOpenStudyMinutes(getStoredOpenStudyMinutes(user))
    }

    refreshOpenStudyMinutes()
    const intervalId = window.setInterval(() => {
      refreshOpenStudyMinutes()
    }, 15000)

    return () => {
      window.clearInterval(intervalId)
    }
  }, [user?.id, user?.email])

  const totalStudyMinutes = (summary?.study_time_minutes ?? 0) + openStudyMinutes

  return (
    <>
      <section className="hero">
        <div className="card">
          <h2 className="page-title">Welcome back, {user?.name || 'student'}</h2>
          <p className="muted">Ask questions, generate quizzes, and track progress in one workspace.</p>
          <div className="metric-grid" style={{ marginTop: 20 }}>
            <div className="card"><strong>{summary?.accuracy ?? 0}%</strong><div className="muted">Average accuracy</div></div>
            <div className="card"><strong>{totalStudyMinutes}</strong><div className="muted">Study minutes</div></div>
          </div>
        </div>
        <div className="card" style={{ minHeight: 320, display: 'grid', placeItems: 'center', background: 'linear-gradient(145deg, rgba(110,168,254,0.18), rgba(47,116,255,0.08))' }}>
          <div style={{ textAlign: 'center' }}>
            <h3 style={{ marginTop: 0 }}>Study momentum</h3>
            <p className="muted">Use the tutor, quizzes, and recommendations together for a structured workflow.</p>
          </div>
        </div>
      </section>
      <section className="feature-grid">
        <ProgressChart values={summary?.quiz_score_trend || []} />
        <div className="card">
          <h3>Recommendations</h3>
          <div style={{ display: 'grid', gap: 12 }}>
            {recommendations.slice(0, 3).map((item) => (
              <RecommendationCard key={`${item.topic}-${item.date_generated}`} topic={item.topic} suggestedMaterial={item.suggested_material} />
            ))}
            {!recommendations.length ? <p className="muted">No recommendations yet. Take a quiz to generate personalized guidance.</p> : null}
          </div>
        </div>
      </section>
    </>
  )
}
