import { useEffect, useMemo, useState } from 'react'
import api from '../services/api'

const starterMessages = [
  { role: 'assistant', text: 'Ask me anything about a topic and I will explain it step by step.' },
]

export default function ChatTutorPage() {
  const [courses, setCourses] = useState([])
  const [messages, setMessages] = useState(starterMessages)
  const [question, setQuestion] = useState('')
  const [topicId, setTopicId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const topics = useMemo(() => courses.flatMap((course) => course.topics.map((topic) => ({ ...topic, courseTitle: course.title }))), [courses])

  useEffect(() => {
    let active = true

    async function loadCourses() {
      try {
        const { data } = await api.get('/courses/')
        if (active) {
          setCourses(data)
          if (!topicId && data[0]?.topics?.[0]?.id) {
            setTopicId(String(data[0].topics[0].id))
          }
        }
      } catch {
        if (active) {
          setError('Unable to load study topics.')
        }
      }
    }

    loadCourses()
    return () => {
      active = false
    }
  }, [])

  async function handleSubmit(event) {
    event.preventDefault()
    if (!question.trim()) return
    setLoading(true)
    setError('')
    setMessages((current) => [...current, { role: 'user', text: question }])

    try {
      const { data } = await api.post('/ai/ask', {
        question,
        topic_id: topicId ? Number(topicId) : undefined,
      })

      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          text: data.answer,
          examples: data.examples,
          related_topics: data.related_topics,
        },
      ])
      setQuestion('')
    } catch {
      setError('Unable to get an AI response right now.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="card">
      <h2 className="page-title">AI Chat Tutor</h2>
      <p className="muted">Structured answers, examples, and related topics will come from the backend AI endpoint.</p>
      <div className="muted" style={{ marginTop: 10 }}>
        Topics loaded: {topics.length}
      </div>
      <div className="chat-window" style={{ marginTop: 20 }}>
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            <div>{message.text}</div>
            {message.examples ? (
              <div style={{ marginTop: 8 }}>
                <strong>Examples</strong>
                <ul>
                  {message.examples.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </div>
            ) : null}
            {message.related_topics ? (
              <div style={{ marginTop: 8 }}>
                <strong>Related topics</strong>
                <div>{message.related_topics.join(', ')}</div>
              </div>
            ) : null}
          </div>
        ))}
      </div>
      <form className="form-row" style={{ marginTop: 20 }} onSubmit={handleSubmit}>
        <select className="select" value={topicId} onChange={(event) => setTopicId(event.target.value)} style={{ maxWidth: 260 }}>
          <option value="">General study help</option>
          {topics.map((topic) => (
            <option key={topic.id} value={topic.id}>{topic.courseTitle} - {topic.title}</option>
          ))}
        </select>
        <input className="input" placeholder="Ask an academic question..." value={question} onChange={(event) => setQuestion(event.target.value)} />
        <button className="button" type="submit" disabled={loading}>{loading ? 'Thinking...' : 'Send'}</button>
      </form>
      {error ? <div style={{ color: '#ff8b92', marginTop: 12 }}>{error}</div> : null}
    </section>
  )
}
