import { useEffect, useMemo, useState } from 'react'
import api from '../services/api'

export default function KnowledgeBasePage() {
  const [documents, setDocuments] = useState([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [form, setForm] = useState({ title: '', tags: '', file: null })

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
      const tags = form.tags
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean)
      tags.forEach((tag) => payload.append('tags', tag))

      await api.post('/knowledge/documents', payload, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setForm({ title: '', tags: '', file: null })
      await loadDocuments()
    } catch (uploadError) {
      const message = uploadError.response?.data?.error_message || 'Upload failed. Check file type and try again.'
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
      <h2 className="page-title">Knowledge Base</h2>
      <p className="muted">Upload private study material to power AI tutoring and quizzes.</p>

      <form className="card" style={{ marginTop: 20, display: 'grid', gap: 12 }} onSubmit={handleUpload}>
        <input
          className="input"
          placeholder="Document title (optional)"
          value={form.title}
          onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
        />
        <input
          className="input"
          placeholder="Tags (comma separated)"
          value={form.tags}
          onChange={(event) => setForm((current) => ({ ...current, tags: event.target.value }))}
        />
        <input
          className="input"
          type="file"
          accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg"
          onChange={(event) => setForm((current) => ({ ...current, file: event.target.files?.[0] || null }))}
        />
        <button className="button" type="submit" disabled={busy}>
          {busy ? 'Processing...' : 'Upload to KB'}
        </button>
      </form>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 20 }}>
        <h3 style={{ margin: 0 }}>My Documents</h3>
        <button className="button" type="button" disabled={busy || !documents.length} onClick={deleteAllDocuments}>
          Delete All
        </button>
      </div>

      {error ? <div style={{ color: '#ff8b92', marginTop: 12 }}>{error}</div> : null}

      <div className="feature-grid" style={{ marginTop: 16 }}>
        {sortedDocs.map((doc) => (
          <article key={doc.id} className="card">
            <h3>{doc.title}</h3>
            <div className="muted">{doc.source_type.toUpperCase()} · {doc.chunk_count} chunks</div>
            <div className="muted">Status: {doc.status}</div>
            {doc.tags?.length ? <div className="muted">Tags: {doc.tags.join(', ')}</div> : null}
            {doc.error_message ? <p style={{ color: '#ff8b92' }}>{doc.error_message}</p> : null}
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
