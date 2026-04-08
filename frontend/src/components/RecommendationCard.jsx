export default function RecommendationCard({ topic = 'General review', suggestedMaterial = 'Review class notes' }) {
  return (
    <div className="card">
      <strong>{topic}</strong>
      <div className="muted">{suggestedMaterial}</div>
    </div>
  )
}
