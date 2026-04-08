import { useEffect, useState } from 'react'
import RecommendationCard from '../components/RecommendationCard'
import api from '../services/api'

export default function RecommendationsPage() {
  const [recommendations, setRecommendations] = useState([])

  useEffect(() => {
    api.get('/recommendations/').then(({ data }) => setRecommendations(data)).catch(() => setRecommendations([]))
  }, [])

  return (
    <section className="card">
      <h2 className="page-title">Recommendations</h2>
      <p className="muted">Personalized study recommendations based on recent performance.</p>
      <div className="feature-grid" style={{ marginTop: 20 }}>
        {recommendations.map((item) => (
          <RecommendationCard key={`${item.topic}-${item.date_generated}`} topic={item.topic} suggestedMaterial={item.suggested_material} />
        ))}
      </div>
      {!recommendations.length ? <p className="muted">No recommendations yet.</p> : null}
    </section>
  )
}
