import { useCallback, useEffect, useState } from 'react'
import * as api from './api.js'
import TaskForm from './TaskForm.jsx'
import TaskList from './TaskList.jsx'
import StatsBar from './StatsBar.jsx'

const EMPTY_FILTERS = { status: '', priority: '', search: '' }

export default function App() {
  const [tasks, setTasks] = useState([])
  const [stats, setStats] = useState(null)
  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [editing, setEditing] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  // Reloads both the list and the counters. Called after every mutation so the
  // UI always reflects what the database actually holds, rather than guessing.
  const refresh = useCallback(async () => {
    try {
      const [taskData, statData] = await Promise.all([api.listTasks(filters), api.getStats()])
      setTasks(taskData)
      setStats(statData)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    refresh()
  }, [refresh])

  const guard = (fn) => async (...args) => {
    try {
      await fn(...args)
      await refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  const handleSave = guard(async (data) => {
    if (editing) {
      await api.updateTask(editing.id, data)
      setEditing(null)
    } else {
      await api.createTask(data)
    }
  })

  const handleComplete = guard(api.completeTask)
  const handleDelete = guard(async (id) => {
    if (window.confirm('Delete this task?')) await api.deleteTask(id)
  })

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Taskr</h1>
          <p className="subtitle">Task tracking for the DevOps capstone</p>
        </div>
      </header>

      {error && (
        <div className="banner error" role="alert">
          <strong>Request failed.</strong> {error}
          <button onClick={() => setError(null)} aria-label="Dismiss">×</button>
        </div>
      )}

      <StatsBar stats={stats} />

      <TaskForm
        key={editing?.id ?? 'new'}
        initial={editing}
        onSave={handleSave}
        onCancel={() => setEditing(null)}
      />

      <section className="filters" aria-label="Filters">
        <input
          type="search"
          placeholder="Search titles…"
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
        />
        <select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          aria-label="Filter by status"
        >
          <option value="">All statuses</option>
          <option value="todo">To do</option>
          <option value="in_progress">In progress</option>
          <option value="done">Done</option>
        </select>
        <select
          value={filters.priority}
          onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
          aria-label="Filter by priority"
        >
          <option value="">All priorities</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <button className="ghost" onClick={() => setFilters(EMPTY_FILTERS)}>
          Reset
        </button>
      </section>

      {loading ? (
        <p className="empty">Loading…</p>
      ) : (
        <TaskList
          tasks={tasks}
          onEdit={setEditing}
          onComplete={handleComplete}
          onDelete={handleDelete}
        />
      )}
    </div>
  )
}
