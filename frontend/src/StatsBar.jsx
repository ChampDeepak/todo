export default function StatsBar({ stats }) {
  if (!stats) return null
  const cards = [
    { label: 'Total', value: stats.total },
    { label: 'To do', value: stats.todo },
    { label: 'In progress', value: stats.in_progress },
    { label: 'Done', value: stats.done },
    { label: 'Overdue', value: stats.overdue, warn: stats.overdue > 0 },
    { label: 'Complete', value: `${stats.completion_rate}%` },
  ]
  return (
    <section className="stats" aria-label="Task statistics">
      {cards.map((c) => (
        <div key={c.label} className={`stat${c.warn ? ' warn' : ''}`}>
          <span className="stat-value">{c.value}</span>
          <span className="stat-label">{c.label}</span>
        </div>
      ))}
    </section>
  )
}
