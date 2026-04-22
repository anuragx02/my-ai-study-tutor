import { useEffect, useState, useRef } from 'react'
import api from '../services/api'
import { fileToDataUrl, isValidImageFile } from '../utils/imageConverter'

const starterMessages = [{ role: 'assistant', text: 'Ask me anything about a topic and I will explain it step by step.' }]

export default function ChatTutorPage() {
  const [sessions, setSessions] = useState([])
  const [currentSessionId, setCurrentSessionId] = useState(null)
  const [messages, setMessages] = useState(starterMessages)
  const [question, setQuestion] = useState('')
  const [forceWeb, setForceWeb] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [processingImage, setProcessingImage] = useState(false)
  const fileInputRef = useRef(null)

  async function loadSessions() {
    try {
      const { data } = await api.get('/ai/sessions')
      const next = data || []
      setSessions(next)
      return next
    } catch {
      setSessions([])
      return []
    }
  }

  async function openSession(sessionId) {
    setCurrentSessionId(sessionId)
    setError('')
    try {
      const { data } = await api.get(`/ai/sessions/${sessionId}`)
      const serverMessages = data.messages.map((message) => ({
        role: message.role,
        text: message.text,
        examples: message.examples,
        related_topics: message.related_topics,
        source_type: message.source_type,
      }))
      setMessages(serverMessages.length ? serverMessages : starterMessages)
    } catch {
      setError('Request failed.')
    }
  }

  async function deleteSession(sessionId) {
    if (!window.confirm('Delete this conversation? This cannot be undone.')) return

    try {
      await api.delete(`/ai/sessions/${sessionId}`)
      const remaining = sessions.filter((session) => session.id !== sessionId)
      setSessions(remaining)
      if (currentSessionId !== sessionId) return
      if (remaining.length) {
        await openSession(remaining[0].id)
      } else {
        setCurrentSessionId(null)
        setMessages(starterMessages)
        setQuestion('')
        setError('')
        setForceWeb(false)
      }
    } catch {
      setError('Request failed.')
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
        setCurrentSessionId(null)
        setMessages(starterMessages)
        setQuestion('')
        setError('')
        setForceWeb(false)
      }
    }
    initialize()
    return () => {
      active = false
    }
  }, [])

  async function handleImageUpload(event) {
    const file = event.target.files[0]
    if (!file || !isValidImageFile(file)) {
      setError('Please upload a valid image file (JPEG, PNG, GIF, WebP)')
      return
    }

    setProcessingImage(true)
    setError('')
    try {
      const dataUrl = await fileToDataUrl(file)
      const { data } = await api.post('/ai/ocr/equation', {
        image_url: dataUrl,
      })
      setQuestion((current) => (current ? `${current} ${data.latex}` : data.latex))
    } catch {
      setError('Request failed.')
    } finally {
      setProcessingImage(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

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
        force_web: forceWeb,
      }
      const { data } = await api.post('/ai/ask', payload)

      await openSession(data.session_id)
      await loadSessions()
    } catch {
      setError('Request failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="card">
      <h2 className="page-title">AI Chat Tutor</h2>
      <p className="muted">Ask tutor questions directly, or turn on web mode for current information.</p>

      <div className="chat-layout" style={{ marginTop: 20 }}>
        <aside className="card chat-sessions" style={{ padding: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <strong>Past Conversations</strong>
            <button
              className="button"
              type="button"
              onClick={() => {
                setCurrentSessionId(null)
                setMessages(starterMessages)
                setQuestion('')
                setError('')
                setForceWeb(false)
              }}
            >
              New chat
            </button>
          </div>
          <div style={{ marginTop: 12, display: 'grid', gap: 8 }}>
            {!sessions.length ? <div className="muted">No past sessions yet.</div> : sessions.map((session) => {
              const active = currentSessionId === session.id
              return (
                <div
                  key={session.id}
                  className="card"
                  style={{ padding: 10, borderColor: active ? 'rgba(123, 199, 255, 0.7)' : undefined, background: active ? 'rgba(46, 139, 255, 0.12)' : undefined }}
                >
                  <button
                    type="button"
                    onClick={() => openSession(session.id)}
                    style={{ width: '100%', border: 0, padding: 0, background: 'transparent', color: 'inherit', textAlign: 'left', cursor: 'pointer' }}
                  >
                    <div className="chat-session-title">{session.title}</div>
                    <div className="muted chat-session-preview" style={{ marginTop: 4, fontSize: 13 }}>{session.last_message_preview || 'No messages yet'}</div>
                  </button>
                  <div style={{ marginTop: 10, display: 'flex', justifyContent: 'flex-end' }}>
                    <button type="button" className="button" onClick={() => deleteSession(session.id)}>Delete</button>
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
                {message.role === 'assistant' ? <div className="debug-tag"><span className="debug-tag__item">path: {message.source_type || 'none'}</span></div> : null}
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
            <input className="input" placeholder={forceWeb ? 'Ask for live/current info...' : 'Ask anything...'} value={question} onChange={(event) => setQuestion(event.target.value)} />
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              style={{ display: 'none' }}
            />
            <button
              type="button"
              className="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={loading || processingImage}
              title="Attach equation image"
              style={{ minWidth: 44, padding: '6px 8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            >
              {processingImage ? <span>⏳</span> : <span style={{ fontSize: 20 }}>📷</span>}
            </button>
            <button
              type="button"
              className="button"
              onClick={() => setForceWeb((current) => !current)}
              style={{
                minWidth: 122,
                background: forceWeb ? 'linear-gradient(135deg, #ffce73, #ff8e3c)' : 'linear-gradient(135deg, #6ea8fe, #2f74ff)',
              }}
            >
              {forceWeb ? 'Web on' : 'Web off'}
            </button>
            <button className="button" type="submit" disabled={loading || processingImage}>{loading ? 'Thinking...' : 'Send'}</button>
          </form>
          <div className="muted" style={{ marginTop: 10, fontSize: 13 }}>
            {processingImage ? 'Processing equation image...' : `Web search ${forceWeb ? 'is enabled' : 'is disabled'}.`}
          </div>
          {error ? <div style={{ color: '#ff8b92', marginTop: 12 }}>{error}</div> : null}
        </div>
      </div>
    </section>
  )
}
