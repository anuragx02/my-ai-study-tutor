import { useRef, useState } from 'react'
import QuizCard from '../components/QuizCard'
import api from '../services/api'

export default function QuizPage() {
  const [focus, setFocus] = useState('')
  const [difficulty, setDifficulty] = useState('easy')
  const [totalQuestions, setTotalQuestions] = useState(5)
  const [quiz, setQuiz] = useState(null)
  const [answers, setAnswers] = useState({})
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [activeExplanation, setActiveExplanation] = useState(null)
  const startedAtRef = useRef(0)

  async function generateQuiz(event) {
    event.preventDefault()
    setError('')
    setResult(null)
    try {
      const { data } = await api.post('/quiz/generate', {
        focus,
        difficulty,
        total_questions: Number(totalQuestions),
      })
      setQuiz(data)
      startedAtRef.current = Date.now()
      setAnswers({})
    } catch {
      setError('Request failed.')
    }
  }

  async function submitQuiz() {
    const elapsedSeconds = Math.max(1, Math.floor((Date.now() - startedAtRef.current) / 1000))
    const payload = {
      quiz_id: quiz.id,
      completion_time: elapsedSeconds,
      answers: quiz.questions.map((question) => ({
        question_id: question.id,
        selected_option: answers[question.id],
      })),
    }
    const { data } = await api.post('/quiz/submit', payload)
    setResult(data)
  }

  return (
    <section className="card">
      <h2 className="page-title">Quiz Interface</h2>
      <p className="muted">Generate quizzes by topic and submit for scoring.</p>

      <form className="feature-grid" style={{ marginTop: 20 }} onSubmit={generateQuiz}>
        <input className="input" placeholder="Quiz focus (optional)" value={focus} onChange={(event) => setFocus(event.target.value)} />
        <select className="select" value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
        <input className="input" type="number" min="1" max="20" value={totalQuestions} onChange={(event) => setTotalQuestions(event.target.value)} />
        <button className="button" type="submit">Generate quiz</button>
      </form>

      {error ? <div style={{ color: '#ff8b92', marginTop: 12 }}>{error}</div> : null}

      {quiz ? (
        <div style={{ marginTop: 24 }}>
          <QuizCard title={quiz.topic_title || quiz.topic} difficulty={quiz.difficulty} totalQuestions={quiz.total_questions} />
          <div style={{ display: 'grid', gap: 16, marginTop: 16 }}>
            {quiz.questions.map((question, index) => (
              <article key={question.id} className="card">
                <strong>{index + 1}. {question.question_text}</strong>
                <div className="feature-grid" style={{ marginTop: 12 }}>
                  {['A', 'B', 'C', 'D'].map((option) => (
                    <label key={option} className="card" style={{ padding: 12 }}>
                      <input
                        type="radio"
                        name={`question-${question.id}`}
                        value={option}
                        checked={answers[question.id] === option}
                        onChange={() => setAnswers((current) => ({ ...current, [question.id]: option }))}
                      />{' '}
                      {question[`option_${option.toLowerCase()}`]}
                    </label>
                  ))}
                </div>
              </article>
            ))}
          </div>
          <button className="button" type="button" style={{ marginTop: 20 }} onClick={submitQuiz}>Submit quiz</button>
        </div>
      ) : null}

      {result ? (
        <div className="card" style={{ marginTop: 20 }}>
          <h3>Result</h3>
          <p><strong>{result.score}%</strong> score • {result.correct_count} correct • {result.incorrect_count} incorrect</p>
          <p><strong>Recommendation:</strong> {result.study_recommendation}</p>

          <div style={{ marginTop: 16, display: 'grid', gap: 12 }}>
            {(result.question_reviews || []).map((review, index) => (
              <article key={review.question_id} className="card" style={{ borderColor: review.is_correct ? 'rgba(60, 197, 131, 0.45)' : 'rgba(255, 139, 146, 0.45)' }}>
                <strong>{index + 1}. {review.question_text}</strong>
                <div style={{ marginTop: 8 }}>
                  <div><strong>Your answer:</strong> {review.selected_option || 'Not answered'}{review.selected_option_text ? ` - ${review.selected_option_text}` : ''}</div>
                  <div><strong>Correct answer:</strong> {review.correct_option} - {review.correct_option_text}</div>
                </div>
                <button
                  type="button"
                  className="button"
                  style={{ marginTop: 10 }}
                  onClick={() => setActiveExplanation({
                    question: review.question_text,
                    explanation: review.explanation,
                  })}
                >
                  Show explanation
                </button>
              </article>
            ))}
          </div>
        </div>
      ) : null}

      {activeExplanation ? (
        <div role="dialog" aria-modal="true" style={{ position: 'fixed', inset: 0, background: 'rgba(5, 10, 25, 0.7)', display: 'grid', placeItems: 'center', zIndex: 1000, padding: 16 }} onClick={() => setActiveExplanation(null)}>
          <div className="card" style={{ maxWidth: 640, width: '100%' }} onClick={(event) => event.stopPropagation()}>
            <h3 style={{ marginTop: 0 }}>Explanation</h3>
            <p className="muted"><strong>Question:</strong> {activeExplanation.question}</p>
            <p>{activeExplanation.explanation}</p>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button type="button" className="button" onClick={() => setActiveExplanation(null)}>Close</button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  )
}
