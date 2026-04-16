import { useEffect, useState } from 'react'
import ProgressChart from '../components/ProgressChart'
import RecommendationCard from '../components/RecommendationCard'
import api from '../services/api'

const emptyProgress = {
  quiz_score_trend: [],
  accuracy: 0,
  weak_topics: [],
  study_time_minutes: 0,
}

export default function InsightsPage() {
  const [progress, setProgress] = useState(emptyProgress)
  const [recommendations, setRecommendations] = useState([])

  useEffect(() => {
    let active = true

    async function loadInsights() {
      try {
        const [progressResponse, recommendationsResponse] = await Promise.all([
          api.get('/analytics/progress'),
          api.get('/recommendations/'),
        ])

        if (!active) return
        setProgress(progressResponse.data || emptyProgress)
        setRecommendations(recommendationsResponse.data || [])
      } catch {
        if (!active) return
        setProgress(emptyProgress)
        setRecommendations([])
      }
    }

    loadInsights()
    return () => {
      active = false
    }
  }, [])

  return (
    <section className="card">
      <h2 className="page-title">Insights</h2>
      <p className="muted">Your learning analytics and recommendations in one place.</p>

      <div className="metric-grid" style={{ marginTop: 20 }}>
        <div className="card"><strong>{progress.accuracy ?? 0}%</strong><div className="muted">Accuracy</div></div>
        <div className="card"><strong>{progress.weak_topics?.length ?? 0}</strong><div className="muted">Weak topics</div></div>
        <div className="card"><strong>{progress.study_time_minutes ?? 0}</strong><div className="muted">Study minutes</div></div>
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
    </section>
  )
}
