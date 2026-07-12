import type { CalendarData, Dream, Health, Insights, User } from '../types'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(path, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const j = await res.json()
      detail = j.detail || j.msg || detail
    } catch { /* ignore */ }
    throw new Error(detail)
  }
  const json = await res.json()
  return json.data as T
}

export interface CreateDreamBody {
  fragments: { type: string; content: string }[]
  emotion?: { label?: string; intensity?: number } | null
  dream_date?: string | null
  title?: string | null
}

export const api = {
  health: () => request<Health>('/api/health'),
  // 账号
  me: () => request<User | null>('/api/auth/me'),
  login: (username: string, password: string) =>
    request<User>('/api/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
  register: (username: string, password: string, display_name?: string) =>
    request<User>('/api/auth/register', { method: 'POST', body: JSON.stringify({ username, password, display_name }) }),
  logout: () => request<{ ok: boolean }>('/api/auth/logout', { method: 'POST' }),
  // 梦境
  createDream: (body: CreateDreamBody) =>
    request<Dream>('/api/dreams', { method: 'POST', body: JSON.stringify(body) }),
  generate: (id: string) => request<Dream>(`/api/dreams/${id}/generate`, { method: 'POST' }),
  regenerate: (id: string) => request<Dream>(`/api/dreams/${id}/regenerate`, { method: 'POST' }),
  listDreams: () => request<Dream[]>('/api/dreams'),
  getDream: (id: string) => request<Dream>(`/api/dreams/${id}`),
  calendar: (month: string) => request<CalendarData>(`/api/dreams/calendar?month=${month}`),
  patchDream: (id: string, body: { title?: string; emotions?: { label: string; intensity: number }[] }) =>
    request<Dream>(`/api/dreams/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteDream: (id: string) => request<{ deleted: string }>(`/api/dreams/${id}`, { method: 'DELETE' }),
  showcase: () => request<Dream | null>('/api/showcase'),
  insights: () => request<Insights>('/api/insights'),
}
