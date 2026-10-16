const STATUS_LABEL = { todo: 'To do', in_progress: 'In progress', done: 'Done' }

function isOverdue(task) {
  return task.due_date && task.status !== 'done' && task.due_date < new Date().toISOString().slice(0, 10)
}

export default function TaskList({ tasks, onEdit, onComplete, onDelete }) {
  if (!tasks.length) {
    return <p className="empty">No tasks match. Add one above, or reset the filters.</p>
  }
  return (
    <ul className="task-list">
      {tasks.map((task) => (
        <li key={task.id} className={`task ${task.status} p-${task.priority}`}>
          <div className="task-main">
            <div className="task-title">
              <span className={task.status === 'done' ? 'struck' : ''}>{task.title}</span>
              <span className={`pill pr-${task.priority}`}>{task.priority}</span>
              <span className="pill st">{STATUS_LABEL[task.status]}</span>
              {isOverdue(task) && <span className="pill overdue">overdue</span>}
            </div>
            {task.description && <p className="task-desc">{task.description}</p>}
            <p className="task-meta">
              #{task.id}
              {task.due_date && <> · due {task.due_date}</>}
            </p>
          </div>
          <div className="task-actions">
            {task.status !== 'done' && (
              <button onClick={() => onComplete(task.id)} title="Mark complete">Done</button>
            )}
            <button onClick={() => onEdit(task)}>Edit</button>
            <button className="danger" onClick={() => onDelete(task.id)}>Delete</button>
          </div>
        </li>
      ))}
    </ul>
  )
}
