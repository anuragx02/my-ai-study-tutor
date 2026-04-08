import { useEffect, useState } from 'react'
import ProgressChart from '../components/ProgressChart'
import api from '../services/api'

export default function AnalyticsPage() {
  const [progress, setProgress] = useState(null)

  useEffect(() => {
    api.get('/analytics/progress').then(({ data }) => setProgress(data)).catch(() => setProgress({ quiz_score_trend: [], accuracy: 0, weak_topics: [], study_time_minutes: 0 }))
  }, [])

  return (
    <section className="card">
      <h2 className="page-title">Analytics Dashboard</h2>
      <p className="muted">Progress tracking scaffold.</p>
      <div className="metric-grid" style={{ marginTop: 20 }}>
        <div className="card"><strong>{progress?.accuracy ?? 0}%</strong><div className="muted">Accuracy</div></div>
        <div className="card"><strong>{progress?.weak_topics?.length ?? 0}</strong><div className="muted">Weak topics</div></div>
        <div className="card"><strong>{progress?.study_time_minutes ?? 0}</strong><div className="muted">Study minutes</div></div>
      </div>
      <div style={{ marginTop: 20 }}>
        <ProgressChart values={progress?.quiz_score_trend || []} />
      </div>
    </section>
  )
}
