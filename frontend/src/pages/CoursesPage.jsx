import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../services/api'

export default function CoursesPage() {
  const { user } = useAuth()
  const [courses, setCourses] = useState([])
  const [form, setForm] = useState({ title: '', description: '' })
  const [topicForm, setTopicForm] = useState({ course: '', title: '', difficulty: 'easy' })
  const [error, setError] = useState('')

  const canEdit = Boolean(user?.is_staff)

  const topics = useMemo(() => courses.flatMap((course) => course.topics.map((topic) => ({ ...topic, courseTitle: course.title }))), [courses])

  useEffect(() => {
    let active = true
    async function loadCourses() {
      try {
        const { data } = await api.get('/courses/')
        if (active) {
          setCourses(data)
          if (!topicForm.course && data[0]?.id) {
            setTopicForm((current) => ({ ...current, course: String(data[0].id) }))
          }
        }
      } catch {
        if (active) setError('Unable to load courses.')
      }
    }
    loadCourses()
    return () => { active = false }
  }, [])

  async function createCourse(event) {
    event.preventDefault()
    const { data } = await api.post('/courses/', form)
    setCourses((current) => [...current, { ...data, topics: [] }])
    setForm({ title: '', description: '' })
  }

  async function createTopic(event) {
    event.preventDefault()
    const { data } = await api.post('/courses/topics', { ...topicForm, course: Number(topicForm.course) })
    setCourses((current) => current.map((course) => course.id === data.course ? { ...course, topics: [...course.topics, data] } : course))
    setTopicForm((current) => ({ ...current, title: '' }))
  }

  return (
    <section className="card">
      <h2 className="page-title">Courses</h2>
      <p className="muted">Browse courses and topics.</p>
      {error ? <div style={{ color: '#ff8b92' }}>{error}</div> : null}
      {canEdit ? (
        <div className="feature-grid" style={{ marginTop: 20 }}>
          <form className="card" onSubmit={createCourse} style={{ display: 'grid', gap: 12 }}>
            <strong>Create course</strong>
            <input className="input" placeholder="Course title" value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} />
            <textarea className="textarea" placeholder="Description" rows="4" value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} />
            <button className="button" type="submit">Save course</button>
          </form>
          <form className="card" onSubmit={createTopic} style={{ display: 'grid', gap: 12 }}>
            <strong>Create topic</strong>
            <select className="select" value={topicForm.course} onChange={(event) => setTopicForm((current) => ({ ...current, course: event.target.value }))}>
              {courses.map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}
            </select>
            <input className="input" placeholder="Topic title" value={topicForm.title} onChange={(event) => setTopicForm((current) => ({ ...current, title: event.target.value }))} />
            <select className="select" value={topicForm.difficulty} onChange={(event) => setTopicForm((current) => ({ ...current, difficulty: event.target.value }))}>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
            <button className="button" type="submit">Save topic</button>
          </form>
        </div>
      ) : null}

      <div className="feature-grid" style={{ marginTop: 20 }}>
        {courses.map((course) => (
          <article key={course.id} className="card">
            <h3>{course.title}</h3>
            <p className="muted">{course.description}</p>
            <div className="muted">{course.topic_count || course.topics?.length || 0} topics</div>
            <ul>
              {course.topics?.map((topic) => <li key={topic.id}>{topic.title} · {topic.difficulty}</li>)}
            </ul>
          </article>
        ))}
      </div>
      {!courses.length ? <p className="muted">No courses yet.</p> : null}
      {topics.length ? <p className="muted">Total topics: {topics.length}</p> : null}
    </section>
  )
}
