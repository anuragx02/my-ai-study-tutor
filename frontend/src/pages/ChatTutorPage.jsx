import { useEffect, useState } from 'react'
import api from '../services/api'
import CitationCard from '../components/CitationCard'

const starterMessages = [
  { role: 'assistant', text: 'Ask me anything about a topic and I will explain it step by step.' },
]

const CITATION_CONFIDENCE_MIN = 0.65

export default function ChatTutorPage() {
  const [sessions, setSessions] = useState([])
  const [currentSessionId, setCurrentSessionId] = useState(null)
  const [messages, setMessages] = useState(starterMessages)
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingSessions, setLoadingSessions] = useState(false)
  const [error, setError] = useState('')

  function resetToNewChat() {
    setCurrentSessionId(null)
    setMessages(starterMessages)
    setQuestion('')
    setError('')
  }

  async function loadSessions() {
    setLoadingSessions(true)
    try {
      const { data } = await api.get('/ai/sessions')
      setSessions(data || [])
      return data || []
    } catch {
      setSessions([])
      return []
    } finally {
      setLoadingSessions(false)
    }
  }

  async function openSession(sessionId) {
    setCurrentSessionId(sessionId)
    setError('')
    try {
      const { data } = await api.get(`/ai/sessions/${sessionId}`)
      const serverMessages = (data?.messages || []).map((message) => ({
        role: message.role,
        text: message.text,
        examples: message.examples,
        related_topics: message.related_topics,
        citations: message.citations || [],
        retrieval_confidence: message.retrieval_confidence,
        source_type: message.source_type,
      }))
      setMessages(serverMessages.length ? serverMessages : starterMessages)
    } catch {
      setError('Unable to load this conversation right now.')
    }
  }

  async function deleteSession(sessionId) {
    const confirmed = window.confirm('Delete this conversation? This cannot be undone.')
    if (!confirmed) return

    try {
      await api.delete(`/ai/sessions/${sessionId}`)

      const remaining = sessions.filter((session) => session.id !== sessionId)
      setSessions(remaining)

      if (currentSessionId === sessionId) {
        if (remaining.length) {
          await openSession(remaining[0].id)
        } else {
          resetToNewChat()
        }
      }
    } catch {
      setError('Unable to delete this conversation right now.')
    }
  }

  useEffect(() => {
    let active = true

    async function initialize() {
      const allSessions = await loadSessions()
      if (!active) return
      if (allSessions.length) {
        await openSession(allSessions[0].id)
      } else {
        resetToNewChat()
      }
    }

    initialize()
    return () => {
      active = false
    }
  }, [])

  async function handleSubmit(event) {
    event.preventDefault()
    if (!question.trim()) return

    const prompt = question.trim()
    setLoading(true)
    setError('')
    setQuestion('')
    setMessages((current) => [...current, { role: 'user', text: prompt }])

    try {
      const payload = {
        question: prompt,
        ...(currentSessionId ? { session_id: currentSessionId } : {}),
      }
      const { data } = await api.post('/ai/ask', payload)

      await openSession(data.session_id)
      await loadSessions()
    } catch {
      setError('Unable to get an AI response right now.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="card">
      <h2 className="page-title">AI Chat Tutor</h2>
      <p className="muted">Ask questions from your uploaded study material and revisit your past conversations any time.</p>

      <div className="chat-layout" style={{ marginTop: 20 }}>
        <aside className="card chat-sessions" style={{ padding: 12, maxHeight: 560, overflow: 'auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <strong>Past Conversations</strong>
            <button className="button" type="button" onClick={resetToNewChat}>New chat</button>
          </div>
          <div style={{ marginTop: 12, display: 'grid', gap: 8 }}>
            {loadingSessions ? <div className="muted">Loading conversations...</div> : null}
            {!loadingSessions && !sessions.length ? <div className="muted">No past sessions yet.</div> : null}
            {sessions.map((session) => {
              const active = currentSessionId === session.id
              return (
                <div
                  key={session.id}
                  className="card"
                  style={{
                    padding: 10,
                    borderColor: active ? 'rgba(123, 199, 255, 0.7)' : undefined,
                    background: active ? 'rgba(46, 139, 255, 0.12)' : undefined,
                  }}
                >
                  <button
                    type="button"
                    onClick={() => openSession(session.id)}
                    style={{
                      width: '100%',
                      border: 0,
                      padding: 0,
                      background: 'transparent',
                      color: 'inherit',
                      textAlign: 'left',
                      cursor: 'pointer',
                    }}
                  >
                    <div className="chat-session-title">{session.title}</div>
                    <div className="muted chat-session-preview" style={{ marginTop: 4, fontSize: 13 }}>{session.last_message_preview || 'No messages yet'}</div>
                  </button>
                  <div style={{ marginTop: 10, display: 'flex', justifyContent: 'flex-end' }}>
                    <button
                      type="button"
                      className="button"
                      onClick={() => deleteSession(session.id)}
                      style={{ background: '#ff8b92' }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </aside>

        <div>
          <div className="chat-window">
            {messages.map((message, index) => (
              <div key={index} className={`message ${message.role}`}>
                <div>{message.text}</div>
                {message.role === 'assistant' && message.source_type === 'web' ? (
                  <div className="fallback-notice">Low KB confidence: response includes web fallback sources.</div>
                ) : null}
                {message.role === 'assistant' && message.source_type === 'mixed' ? (
                  <div className="fallback-notice">Mixed sources used: knowledge base and web results.</div>
                ) : null}
                {message.role === 'assistant' && Number.isFinite(Number(message.retrieval_confidence)) ? (
                  <div className="confidence-note muted">
                    Retrieval confidence: {(Number(message.retrieval_confidence) * 100).toFixed(0)}%
                  </div>
                ) : null}
                {message.role === 'assistant' && Number(message.retrieval_confidence) >= CITATION_CONFIDENCE_MIN && message.citations?.length ? (
                  <div className="citations-block">
                    <strong>Sources</strong>
                    <div className="citations-grid">
                      {message.citations.map((citation, citationIndex) => (
                        <CitationCard key={`${index}-${citationIndex}`} citation={citation} />
                      ))}
                    </div>
                  </div>
                ) : null}
                {message.examples?.length ? (
                  <div style={{ marginTop: 8 }}>
                    <strong>Examples</strong>
                    <ul>
                      {message.examples.map((item, exampleIndex) => <li key={`${index}-example-${exampleIndex}`}>{item}</li>)}
                    </ul>
                  </div>
                ) : null}
                {message.related_topics?.length ? (
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
        </div>
      </div>
    </section>
  )
}
