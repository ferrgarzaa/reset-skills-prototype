// In-browser stand-in for the backend, used only by the preview build (VITE_DEMO=1).
// It mirrors the backend's behavior with mocked model replies and keeps data in memory.
// The real app always uses FastAPI + SQLite.
import MOCKS from '../../../backend/app/mock_responses.json'
import { CRISIS_MESSAGE, crisisMatch } from './crisis.js'
import { FALLBACK_STEPS } from './api.js'

const state = {
  sessions: [],
  messages: [],
  prefs: { remember_journal: true, last_sensing: 'none' },
  mode: 'mock',
  n: 0,
}
const now = () => new Date().toISOString()
const wait = (ms) => new Promise((r) => setTimeout(r, ms))

function mock(purpose, text = '', usual = false) {
  state.n += 1
  if (state.mode === 'fail') return null
  if (purpose === 'journal') {
    const low = text.toLowerCase()
    const rule = MOCKS.journal.rules.find((r) => r.match.some((w) => low.includes(w)))
    if (rule) return rule.reply
    return MOCKS.journal.default[state.n % MOCKS.journal.default.length]
  }
  const list = MOCKS[purpose === 'closing' && usual ? 'closing_usual' : purpose]
  return list[state.n % list.length]
}

function usual() {
  const recent = state.sessions.filter((s) => s.kind !== 'journal').slice(-10)
  const counts = {}
  recent.forEach((s) => { if (s.status === 'completed') counts[s.kind] = (counts[s.kind] || 0) + 1 })
  const keys = Object.keys(counts)
  if (!keys.length) return null
  const best = keys.sort((a, b) => counts[b] - counts[a])[0]
  const fb = recent.filter((s) => s.kind === best).slice(-2).map((s) => s.feedback)
  if (fb.length === 2 && fb.every((f) => f === 'not_today')) return null
  return best
}

function addMsg(session_id, role, content, source, purpose = 'chat', crisis_flag = 0) {
  state.messages.push({ session_id, role, content, source, purpose, crisis_flag, created_at: now() })
}

export async function handle(method, path, body) {
  await wait(250)
  const m = path.match(/^\/sessions\/(\d+)(\/\w+)?$/)
  const sid = m ? Number(m[1]) : null
  const sess = sid ? state.sessions.find((s) => s.id === sid) : null

  if (method === 'GET' && path === '/health') return { ok: true, llm: { mode: state.mode } }
  if (method === 'GET' && path === '/home') {
    const line = mock('opening')
    return {
      usual: usual(), last_sensing: state.prefs.last_sensing,
      opening_line: line || 'Take a short reset. Stop whenever you want.',
      opening_source: line ? 'mock' : 'fallback',
      journal_starters: ["What's taking up the most space in my head", 'Something that went okay today', "Something I'm carrying"],
    }
  }
  if (method === 'POST' && path === '/sessions') {
    const s = { id: state.sessions.length + 1, kind: body.skill, started_at: now(), status: 'in_progress',
      sensing: body.sensing, was_usual: body.from_usual ? 1 : 0, feedback: null, duration_s: null }
    state.sessions.push(s)
    if (body.sensing) state.prefs.last_sensing = body.sensing
    return { session_id: s.id, steps: FALLBACK_STEPS[body.skill] }
  }
  if (method === 'POST' && m && m[2] === '/finish') {
    Object.assign(sess, { status: body.status, duration_s: body.duration_s, breaths_detected: body.breaths_detected })
    return { ok: true }
  }
  if (method === 'POST' && m && m[2] === '/closing') {
    const t = mock('closing', '', !!sess.was_usual)
    const line = t || "That's the reset. Take your time."
    addMsg(sid, 'assistant', line, t ? 'mock' : 'fallback', 'closing')
    return { line, source: t ? 'mock' : 'fallback' }
  }
  if (method === 'POST' && m && m[2] === '/feedback') { sess.feedback = body.feedback; return { ok: true } }
  if (method === 'POST' && path === '/journal/message') {
    let id = body.session_id
    if (!id) {
      id = state.sessions.length + 1
      state.sessions.push({ id, kind: 'journal', started_at: now(), status: 'in_progress' })
    }
    const crisis = crisisMatch(body.text)
    addMsg(id, 'user', body.text, 'user', 'chat', crisis ? 1 : 0)
    if (crisis) {
      addMsg(id, 'assistant', CRISIS_MESSAGE, 'static', 'chat', 1)
      return { session_id: id, reply: CRISIS_MESSAGE, source: 'static', crisis: true }
    }
    await wait(500)
    const t = mock('journal', body.text)
    const reply = t || "I'm having trouble replying right now. Your words are saved here. You can keep writing, try a Breath reset, or come back later."
    addMsg(id, 'assistant', reply, t ? 'mock' : 'fallback')
    return { session_id: id, reply, source: t ? 'mock' : 'fallback', crisis: false }
  }
  if (method === 'POST' && path.match(/^\/journal\/\d+\/end$/)) {
    const s = state.sessions.find((x) => x.id === Number(path.split('/')[2]))
    if (s) s.status = 'completed'
    return { ok: true }
  }
  if (method === 'GET' && path === '/history') {
    return {
      sessions: state.sessions
        .filter((s) => s.kind !== 'journal' || state.messages.some((x) => x.session_id === s.id))
        .map((s) => ({ ...s, first_text: state.messages.find((x) => x.session_id === s.id && x.role === 'user')?.content }))
        .reverse(),
    }
  }
  if (method === 'GET' && m && !m[2]) {
    return { session: sess, messages: state.messages.filter((x) => x.session_id === sid) }
  }
  if (method === 'DELETE' && path === '/history') { state.sessions = []; state.messages = []; return { ok: true } }
  if (method === 'GET' && path === '/prefs') return { remember_journal: state.prefs.remember_journal }
  if (method === 'PUT' && path === '/prefs') { state.prefs.remember_journal = body.remember_journal; return { ok: true } }
  if (method === 'POST' && path === '/dev/llm-mode') { state.mode = body.mode === 'fail' ? 'fail' : 'mock'; return { mode: state.mode } }
  throw new Error(`demo: no route ${method} ${path}`)
}
