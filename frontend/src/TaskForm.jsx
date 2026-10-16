import { useState } from 'react'

const blank = { title: '', description: '', status: 'todo', priority: 'medium', due_date: '' }

export default function TaskForm({ initial, onSave, onCancel }) {
  const [form, setForm] = useState(
    initial ? { ...blank, ...initial, due_date: initial.due_date ?? '' } : blank,
  )
  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const submit = (e) => {
    e.preventDefault()
    if (!form.title.trim()) return
    // due_date must be null, not "", or the API rejects it as an invalid date.
    onSave({ ...form, due_date: form.due_date || null, description: form.description || null })
    if (!initial) setForm(blank)
  }

  return (
    <form className="task-form" onSubmit={submit}>
      <h2>{initial ? `Edit task #${initial.id}` : 'New task'}</h2>
      <div className="row">
        <input
          className="grow"
          placeholder="What needs doing?"
          value={form.title}
          onChange={set('title')}
          maxLength={200}
          required
        />
      </div>
      <div className="row">
        <textarea
          placeholder="Notes (optional)"
          value={form.description ?? ''}
          onChange={set('description')}
          rows={2}
        />
      </div>
      <div className="row">
        <select value={form.priority} onChange={set('priority')} aria-label="Priority">
          <option value="high">High priority</option>
          <option value="medium">Medium priority</option>
          <option value="low">Low priority</option>
        </select>
        <select value={form.status} onChange={set('status')} aria-label="Status">
          <option value="todo">To do</option>
          <option value="in_progress">In progress</option>
          <option value="done">Done</option>
        </select>
        <input type="date" value={form.due_date ?? ''} onChange={set('due_date')} aria-label="Due date" />
        <button type="submit" className="primary">{initial ? 'Save changes' : 'Add task'}</button>
        {initial && (
          <button type="button" className="ghost" onClick={onCancel}>Cancel</button>
        )}
      </div>
    </form>
  )
}
