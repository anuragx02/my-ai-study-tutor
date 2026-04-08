import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../services/api'

export default function MaterialsPage() {
  const { user } = useAuth()
  const [courses, setCourses] = useState([])
  const [materials, setMaterials] = useState([])
  const [form, setForm] = useState({ topic: '', title: '', material_type: 'pdf', content_url: '', summary: '' })
  const canEdit = user && ['admin', 'tutor'].includes(user.role)

  const topics = useMemo(() => courses.flatMap((course) => course.topics.map((topic) => ({ ...topic, courseTitle: course.title }))), [courses])

  useEffect(() => {
    let active = true
    async function loadData() {
      const [coursesResponse, materialsResponse] = await Promise.all([api.get('/courses/'), api.get('/materials/')])
      if (active) {
        setCourses(coursesResponse.data)
        setMaterials(materialsResponse.data)
        if (!form.topic && coursesResponse.data[0]?.topics?.[0]?.id) {
          setForm((current) => ({ ...current, topic: String(coursesResponse.data[0].topics[0].id) }))
        }
      }
    }

    loadData().catch(() => {})
    return () => { active = false }
  }, [])

  async function createMaterial(event) {
    event.preventDefault()
    const { data } = await api.post('/materials/', { ...form, topic: Number(form.topic) })
    setMaterials((current) => [data, ...current])
    setForm((current) => ({ ...current, title: '', content_url: '', summary: '' }))
  }

  return (
    <section className="card">
      <h2 className="page-title">Study Materials</h2>
      <p className="muted">Upload or browse PDFs, videos, and notes.</p>
      {canEdit ? (
        <form className="feature-grid" onSubmit={createMaterial} style={{ marginTop: 20 }}>
          <select className="select" value={form.topic} onChange={(event) => setForm((current) => ({ ...current, topic: event.target.value }))}>
            {topics.map((topic) => <option key={topic.id} value={topic.id}>{topic.courseTitle} - {topic.title}</option>)}
          </select>
          <input className="input" placeholder="Material title" value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} />
          <select className="select" value={form.material_type} onChange={(event) => setForm((current) => ({ ...current, material_type: event.target.value }))}>
            <option value="pdf">PDF</option>
            <option value="video">Video</option>
            <option value="notes">Notes</option>
          </select>
          <input className="input" placeholder="Content URL" value={form.content_url} onChange={(event) => setForm((current) => ({ ...current, content_url: event.target.value }))} />
          <textarea className="textarea" placeholder="Summary" rows="3" style={{ gridColumn: '1 / -1' }} value={form.summary} onChange={(event) => setForm((current) => ({ ...current, summary: event.target.value }))} />
          <button className="button" type="submit" style={{ gridColumn: '1 / -1' }}>Save material</button>
        </form>
      ) : null}

      <div className="feature-grid" style={{ marginTop: 20 }}>
        {materials.map((material) => (
          <article key={material.id} className="card">
            <h3>{material.title}</h3>
            <div className="muted">{material.topic_title} · {material.material_type}</div>
            <p>{material.summary}</p>
          </article>
        ))}
      </div>
      {!materials.length ? <p className="muted">No materials yet.</p> : null}
    </section>
  )
}
