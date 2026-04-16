import { useState } from 'react'
import api from '../services/api'

const starterMessages = [
  { role: 'assistant', text: 'Ask me anything about a topic and I will explain it step by step.' },
]

export default function ChatTutorPage() {
  const [messages, setMessages] = useState(starterMessages)
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    if (!question.trim()) return
    setLoading(true)
    setError('')
    setMessages((current) => [...current, { role: 'user', text: question }])

    try {
      const { data } = await api.post('/ai/ask', { question })

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
      <p className="muted">Ask questions from your uploaded study material and get concise tutoring help.</p>
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
        <input className="input" placeholder="Ask an academic question..." value={question} onChange={(event) => setQuestion(event.target.value)} />
        <button className="button" type="submit" disabled={loading}>{loading ? 'Thinking...' : 'Send'}</button>
      </form>
      {error ? <div style={{ color: '#ff8b92', marginTop: 12 }}>{error}</div> : null}
    </section>
  )
}
