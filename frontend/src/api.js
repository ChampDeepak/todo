// All calls use relative paths. Whatever serves this page also proxies /api to
// the backend, so the same built bundle works in dev, in Docker and in K8s.
const BASE = '/api/tasks'

async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${body.slice(0, 200)}`)
  }
  return res.status === 204 ? null : res.json()
}

export const listTasks = (filters = {}) => {
  const qs = new URLSearchParams(
    Object.entries(filters).filter(([, v]) => v !== '' && v != null),
  )
  return request(`${BASE}?${qs}`)
}
export const getStats = () => request(`${BASE}/stats`)
export const createTask = (data) => request(BASE, { method: 'POST', body: JSON.stringify(data) })
export const updateTask = (id, data) =>
  request(`${BASE}/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const completeTask = (id) => request(`${BASE}/${id}/complete`, { method: 'PATCH' })
export const deleteTask = (id) => request(`${BASE}/${id}`, { method: 'DELETE' })
