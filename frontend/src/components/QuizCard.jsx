export default function QuizCard({ title = 'Sample Quiz', difficulty = 'Easy', totalQuestions = 5 }) {
  return (
    <div className="card">
      <strong>{title}</strong>
      <div className="muted">Difficulty: {difficulty}</div>
      <div className="muted">{totalQuestions} questions</div>
    </div>
  )
}
