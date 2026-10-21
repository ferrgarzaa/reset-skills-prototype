// Thin wrapper around the backend. In the demo build (VITE_DEMO=1) the same
// functions run against an in-browser mock so the app can be previewed without a server.
import * as demo from './demoApi.js'

const DEMO = import.meta.env.VITE_DEMO === '1'
const TIMEOUT_MS = 15000

async function request(method, path, body) {
  if (DEMO) return demo.handle(method, path, body)
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS)
  try {
    const res = await fetch(`/api${path}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: ctrl.signal,
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return await res.json()
  } finally {
    clearTimeout(timer)
  }
}

export const api = {
  health: () => request('GET', '/health'),
  home: () => request('GET', '/home'),
  startSession: (skill, sensing, fromUsual) =>
    request('POST', '/sessions', { skill, sensing, from_usual: fromUsual }),
  finishSession: (id, data) => request('POST', `/sessions/${id}/finish`, data),
  closing: (id) => request('POST', `/sessions/${id}/closing`),
  feedback: (id, feedback) => request('POST', `/sessions/${id}/feedback`, { feedback }),
  journalMessage: (sessionId, text) =>
    request('POST', '/journal/message', { session_id: sessionId, text }),
  journalEnd: (id) => request('POST', `/journal/${id}/end`),
  history: () => request('GET', '/history'),
  session: (id) => request('GET', `/sessions/${id}`),
  clearHistory: () => request('DELETE', '/history'),
  prefs: () => request('GET', '/prefs'),
  setPrefs: (p) => request('PUT', '/prefs', p),
  setLlmMode: (mode) => request('POST', '/dev/llm-mode', { mode }),
}

export const IS_DEMO = DEMO

// Used when the backend can't be reached, so the exercise still runs (not saved).
export const FALLBACK_STEPS = {
  breath: [
    { step_order: 1, kind: 'intro', text: 'Follow the circle. In for 4, out for 6.', duration_s: 3 },
    ...Array.from({ length: 6 }, (_, i) => ({
      step_order: i + 2, kind: 'cycle', text: 'In for 4, out for 6.', duration_s: 10,
    })),
    { step_order: 8, kind: 'close', text: "Last breath out. That's it.", duration_s: 3 },
  ],
  ground: [
    { step_order: 1, kind: 'intro', text: 'Look around. One sense at a time, no need to type anything.', duration_s: 3 },
    { step_order: 2, kind: 'sense', text: 'Notice 5 things you can see.', count: 5, duration_s: 15.5 },
    { step_order: 3, kind: 'sense', text: 'Notice 4 things you can feel.', count: 4, duration_s: 13 },
    { step_order: 4, kind: 'sense', text: 'Notice 3 things you can hear.', count: 3, duration_s: 10.5 },
    { step_order: 5, kind: 'sense', text: 'Notice 2 things you can smell.', count: 2, duration_s: 8 },
    { step_order: 6, kind: 'sense', text: 'Notice 1 thing you can taste.', count: 1, duration_s: 5.5 },
  ],
}
