import { useEffect, useState } from 'react'
import ProgressChart from '../components/ProgressChart'
import RecommendationCard from '../components/RecommendationCard'
import api from '../services/api'
import { getStoredOpenStudyMinutes, resetStoredOpenStudySeconds } from '../utils/studyTime'

const emptyProgress = {
  quiz_score_trend: [],
  accuracy: 0,
  weak_topics: [],
  study_time_minutes: 0,
}

export default function InsightsPage() {
  const [progress, setProgress] = useState(emptyProgress)
  const [recommendations, setRecommendations] = useState([])
  const [clearing, setClearing] = useState(false)
  const [openStudyMinutes, setOpenStudyMinutes] = useState(0)

  async function loadInsights() {
    try {
      const [progressResponse, recommendationsResponse] = await Promise.all([
        api.get('/analytics/progress'),
        api.get('/recommendations/'),
      ])

      setProgress(progressResponse.data || emptyProgress)
      setRecommendations(recommendationsResponse.data || [])
    } catch {
      setProgress(emptyProgress)
      setRecommendations([])
    }
  }

  useEffect(() => {
    let active = true

    const wrapper = async () => {
      await loadInsights()
    }
    wrapper()

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    setOpenStudyMinutes(getStoredOpenStudyMinutes())
    const intervalId = window.setInterval(() => {
      setOpenStudyMinutes(getStoredOpenStudyMinutes())
    }, 15000)

    return () => {
      window.clearInterval(intervalId)
    }
  }, [])

  const totalStudyMinutes = (progress.study_time_minutes ?? 0) + openStudyMinutes

  async function handleClearHistory() {
    if (!window.confirm('Clear all quiz attempts? This cannot be undone.')) {
      return
    }

    setClearing(true)
    try {
      await api.delete('/analytics/history')
      resetStoredOpenStudySeconds()
      setOpenStudyMinutes(0)
      setProgress(emptyProgress)
      setRecommendations([])
      alert('Quiz history cleared.')
    } catch (error) {
      alert('Failed to clear history: ' + (error.response?.data?.detail || 'Unknown error'))
    } finally {
      setClearing(false)
    }
  }

  return (
    <section className="card">
      <h2 className="page-title">Insights</h2>
      <p className="muted">Your learning analytics and recommendations in one place.</p>

      <div className="metric-grid" style={{ marginTop: 20 }}>
        <div className="card"><strong>{progress.accuracy ?? 0}%</strong><div className="muted">Accuracy</div></div>
        <div className="card"><strong>{totalStudyMinutes}</strong><div className="muted">Study minutes</div></div>
      </div>

      <div style={{ marginTop: 20 }}>
        <ProgressChart values={progress.quiz_score_trend || []} />
      </div>

      <div style={{ marginTop: 20 }}>
        <h3 style={{ marginTop: 0 }}>Recommendations</h3>
        <div className="feature-grid" style={{ marginTop: 12 }}>
          {recommendations.map((item) => (
            <RecommendationCard
              key={`${item.topic}-${item.date_generated}`}
              topic={item.topic}
              suggestedMaterial={item.suggested_material}
            />
          ))}
        </div>
        {!recommendations.length ? <p className="muted">No recommendations yet. Take a quiz to generate them.</p> : null}
      </div>

      <div style={{ marginTop: 20, paddingTop: 20, borderTop: '1px solid rgba(123, 199, 255, 0.2)' }}>
        <button
          className="button"
          onClick={handleClearHistory}
          disabled={clearing}
          style={{ background: '#ff8b92' }}
        >
          {clearing ? 'Clearing...' : 'Clear history'}
        </button>
        <p className="muted" style={{ marginTop: 8 }}>Clears all quiz attempts and resets analytics.</p>
      </div>
    </section>
  )
}
