import { useEffect, useMemo, useState } from 'react'
import api from '../services/api'

export default function KnowledgeBasePage() {
  const [documents, setDocuments] = useState([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [form, setForm] = useState({ title: '', file: null })

  const sortedDocs = useMemo(
    () => [...documents].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)),
    [documents],
  )

  async function loadDocuments() {
    try {
      const { data } = await api.get('/knowledge/documents')
      setDocuments(data)
    } catch {
      setError('Unable to load knowledge base documents.')
    }
  }

  useEffect(() => {
    loadDocuments()
  }, [])

  async function handleUpload(event) {
    event.preventDefault()
    if (!form.file) {
      setError('Please select a file to upload.')
      return
    }

    setBusy(true)
    setError('')
    try {
      const payload = new FormData()
      payload.append('file', form.file)
      if (form.title.trim()) {
        payload.append('title', form.title.trim())
      }

      await api.post('/knowledge/documents', payload, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setForm({ title: '', file: null })
      await loadDocuments()
    } catch (uploadError) {
      const message = uploadError.response?.data?.detail || 'Upload failed. Check file type and try again.'
      setError(message)
    } finally {
      setBusy(false)
    }
  }

  async function deleteDocument(id) {
    setBusy(true)
    try {
      await api.delete(`/knowledge/documents/${id}`)
      setDocuments((current) => current.filter((item) => item.id !== id))
    } catch {
      setError('Unable to delete document.')
    } finally {
      setBusy(false)
    }
  }

  async function deleteAllDocuments() {
    setBusy(true)
    try {
      await api.delete('/knowledge/documents/purge')
      setDocuments([])
    } catch {
      setError('Unable to delete all documents.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="card">
      <h2 className="page-title">Study Material</h2>
      <p className="muted">Upload PDF or TXT notes, guides, and papers for chat and quizzes.</p>

      <form className="card" style={{ marginTop: 20, display: 'grid', gap: 12 }} onSubmit={handleUpload}>
        <input
          className="input"
          placeholder="Document title (optional)"
          value={form.title}
          onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
        />
        <input
          className="input"
          type="file"
          accept=".pdf,.txt"
          onChange={(event) => setForm((current) => ({ ...current, file: event.target.files?.[0] || null }))}
        />
        <button className="button" type="submit" disabled={busy}>
          {busy ? 'Processing...' : 'Upload Material'}
        </button>
      </form>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 20 }}>
        <h3 style={{ margin: 0 }}>My Materials</h3>
        <button className="button" type="button" disabled={busy || !documents.length} onClick={deleteAllDocuments}>
          Delete All
        </button>
      </div>

      {error ? <div style={{ color: '#ff8b92', marginTop: 12 }}>{error}</div> : null}

      <div className="feature-grid" style={{ marginTop: 16 }}>
        {sortedDocs.map((doc) => (
          <article key={doc.id} className="card">
            <h3>{doc.title}</h3>
            <div className="muted">{doc.file_type.toUpperCase()} · {new Date(doc.created_at).toLocaleDateString()}</div>
            <button className="button" type="button" onClick={() => deleteDocument(doc.id)} disabled={busy}>
              Delete
            </button>
          </article>
        ))}
      </div>

      {!documents.length ? <p className="muted" style={{ marginTop: 16 }}>No documents uploaded yet.</p> : null}
    </section>
  )
}
