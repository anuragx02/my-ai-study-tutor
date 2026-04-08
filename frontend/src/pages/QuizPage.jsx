import { useEffect, useMemo, useState } from 'react'
import QuizCard from '../components/QuizCard'
import api from '../services/api'

export default function QuizPage() {
  const [courses, setCourses] = useState([])
  const [topicId, setTopicId] = useState('')
  const [difficulty, setDifficulty] = useState('easy')
  const [totalQuestions, setTotalQuestions] = useState(5)
  const [quiz, setQuiz] = useState(null)
  const [answers, setAnswers] = useState({})
  const [result, setResult] = useState(null)

  const topics = useMemo(() => courses.flatMap((course) => course.topics.map((topic) => ({ ...topic, courseTitle: course.title }))), [courses])

  useEffect(() => {
    api.get('/courses/').then(({ data }) => {
      setCourses(data)
      if (!topicId && data[0]?.topics?.[0]?.id) {
        setTopicId(String(data[0].topics[0].id))
      }
    }).catch(() => {})
  }, [])

  async function generateQuiz(event) {
    event.preventDefault()
    if (!topicId) return
    setResult(null)
    const { data } = await api.post('/quiz/generate', {
      topic_id: Number(topicId),
      difficulty,
      total_questions: Number(totalQuestions),
    })
    setQuiz(data)
    setAnswers({})
  }

  async function submitQuiz() {
    const payload = {
      quiz_id: quiz.id,
      completion_time: 0,
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
      <p className="muted">Generate topic-based quizzes, answer them, and submit for scoring.</p>

      <form className="feature-grid" style={{ marginTop: 20 }} onSubmit={generateQuiz}>
        <select className="select" value={topicId} onChange={(event) => setTopicId(event.target.value)}>
          {topics.map((topic) => <option key={topic.id} value={topic.id}>{topic.courseTitle} - {topic.title}</option>)}
        </select>
        <select className="select" value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
        <input className="input" type="number" min="1" max="20" value={totalQuestions} onChange={(event) => setTotalQuestions(event.target.value)} />
        <button className="button" type="submit">Generate quiz</button>
      </form>

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
          <div className="metric-grid">
            <div className="card"><strong>{result.score}%</strong><div className="muted">Score</div></div>
            <div className="card"><strong>{result.correct_count}</strong><div className="muted">Correct</div></div>
            <div className="card"><strong>{result.incorrect_count}</strong><div className="muted">Incorrect</div></div>
          </div>
          <p className="muted">Weak topics: {result.weak_topics.join(', ') || 'None'}</p>
        </div>
      ) : null}
    </section>
  )
}
