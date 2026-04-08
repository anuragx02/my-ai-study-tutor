export default function ProgressChart({ values = [] }) {
  return (
    <div className="card">
      <strong>Progress</strong>
      <div className="muted">Trend: {values.join(' → ') || 'No data yet'}</div>
    </div>
  )
}
