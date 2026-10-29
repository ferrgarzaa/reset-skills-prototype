// In-browser stand-in for the backend, used only by the preview build (VITE_DEMO=1).
// It mirrors the backend's behavior with mocked model replies and keeps data in memory.
// The real app always uses FastAPI + SQLite.
import MOCKS from '../../../backend/app/mock_responses.json'
import { CRISIS_MESSAGE, crisisMatch } from './crisis.js'
import { FALLBACK_STEPS } from './api.js'

const state = {
  sessions: [],
  messages: [],
  prefs: { remember_journal: true, last_sensing: 'none', display_name: '', favorite_activity: '', large_text: false },
  checkins: [],
  mode: 'mock',
  n: 0,
}
const now = () => new Date().toISOString()
const wait = (ms) => new Promise((r) => setTimeout(r, ms))

const SKILL = { breath: 'Breath reset', ground: 'Ground reset' }
const CHECK = { wound_up: 'wound up / tense', scattered: 'scattered / hard to focus', low: 'low / heavy', okay: 'okay' }

function recentCheckin() {
  const c = state.checkins[state.checkins.length - 1]
  if (!c || c.state === 'cleared') return null
  return Date.now() - new Date(c.created_at).getTime() < 3 * 3600e3 ? c.state : null
}

function context(sessionId) {
  const lines = []
  const p = state.prefs
  if (p.display_name) lines.push(`They asked to be called: ${p.display_name}.`)
  if (p.favorite_activity) lines.push(`Something they said they enjoy: ${p.favorite_activity}.`)
  const ci = recentCheckin()
  if (ci) lines.push(`At the start of this visit they chose the check-in: ${CHECK[ci]}. This is their own words for right now, not a diagnosis.`)
  const u = usual()
  if (u) lines.push(`Their usual reset: ${SKILL[u]}.`)
  const week = Date.now() - 7 * 864e5
  const done = {}
  state.sessions.filter((s) => s.kind !== 'journal' && s.status === 'completed' && new Date(s.started_at) >= week)
    .forEach((s) => { done[s.kind] = (done[s.kind] || 0) + 1 })
  if (Object.keys(done).length) lines.push('Resets completed in the last 7 days: ' + Object.entries(done).map(([k, n]) => `${SKILL[k]} x${n}`).join(', ') + '.')
  if (p.remember_journal) {
    state.sessions.filter((s) => s.kind === 'journal' && s.id !== sessionId).reverse().slice(0, 3).forEach((s) => {
      const first = state.messages.find((m) => m.session_id === s.id && m.role === 'user' && !m.crisis_flag)
      if (first) lines.push(`Earlier journal entry (${s.started_at.slice(0, 10)}) began: "${first.content.slice(0, 120)}"`)
    })
  } else lines.push('Memory of past journal entries is turned off. Do not refer to past entries.')
  return 'CONTEXT\n' + (lines.length ? lines.join('\n') : 'No earlier activity in the app.')
}

function mock(purpose, text = '', usualFlag = false, sessionId = null) {
  state.n += 1
  if (state.mode === 'fail') return null
  if (purpose === 'journal') {
    const low = text.toLowerCase()
    const rule = MOCKS.journal.rules.find((r) => r.match.some((w) => low.includes(w)))
    let reply = rule ? rule.reply : MOCKS.journal.default[state.n % MOCKS.journal.default.length]
    const u = usual()
    if (u && reply.includes('the Breath reset takes about a minute')) {
      reply = reply.replace('the Breath reset takes about a minute', `your usual ${SKILL[u]} is there and takes about a minute`)
    }
    const first = !state.messages.some((m) => m.session_id === sessionId && m.role === 'assistant')
    if (first && state.prefs.display_name) reply = `Thanks for writing, ${state.prefs.display_name}. ` + reply
    return reply
  }
  const usual_ = usualFlag
  const list = MOCKS[purpose === 'closing' && usual_ ? 'closing_usual' : purpose]
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

function profile() {
  const r = state.sessions.filter((s) => s.kind !== 'journal')
  const by = {}
  r.filter((s) => s.status === 'completed').forEach((s) => { by[s.kind] = (by[s.kind] || 0) + 1 })
  return {
    display_name: state.prefs.display_name, favorite_activity: state.prefs.favorite_activity,
    usual: usual(), checkin: recentCheckin(),
    recent_checkins: state.checkins.filter((c) => c.state !== 'cleared').slice(-5).reverse(),
    last_sensing: state.prefs.last_sensing, large_text: state.prefs.large_text,
    remember_journal: state.prefs.remember_journal,
    resets_completed: r.filter((s) => s.status === 'completed').length,
    resets_stopped: r.filter((s) => s.status === 'stopped').length,
    completed_by_skill: by,
    journal_entries: state.sessions.filter((s) => s.kind === 'journal' && state.messages.some((m) => m.session_id === s.id)).length,
    first_seen: state.sessions[0]?.started_at || null,
  }
}

// Fictional example user for demos. Everything here is made up.
function seed() {
  const ago = (d, h = 0) => new Date(Date.now() - (d * 24 + h) * 3600e3).toISOString()
  state.sessions = []; state.messages = []; state.checkins = []
  Object.assign(state.prefs, { display_name: 'Sofia', favorite_activity: 'running, training for a half marathon', last_sensing: 'hold' })
  const rows = [
    ['breath', 6, 'completed', 66, 'helped'], ['ground', 5, 'completed', 61.2, 'not_sure'],
    ['breath', 3, 'completed', 66, 'helped'], ['breath', 2, 'stopped', 21.4, null], ['breath', 1, 'completed', 66, null],
  ]
  rows.forEach(([kind, d, status, dur, fb]) => state.sessions.push({ id: state.sessions.length + 1, kind, started_at: ago(d), status, duration_s: dur, feedback: fb, was_usual: 0 }))
  const id = state.sessions.length + 1
  state.sessions.push({ id, kind: 'journal', started_at: ago(2, 1), status: 'completed', duration_s: 140 })
  addMsg(id, 'user', "Long run went bad today. My legs felt dead and I'm annoyed at myself.", 'user')
  addMsg(id, 'assistant', "That sounds frustrating after putting in the effort. Rough days happen in training too. What's bugging you most about it?", 'mock')
  ;[[6, 'wound_up'], [5, 'scattered'], [3, 'wound_up'], [1, 'okay']].forEach(([d, st]) => state.checkins.push({ state: st, created_at: ago(d) }))
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
    const t = mock('journal', body.text, false, id)
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
  if (method === 'DELETE' && path === '/history') { state.sessions = []; state.messages = []; state.checkins = []; return { ok: true } }
  if (method === 'POST' && path === '/checkin') {
    state.checkins.push({ state: body.state, created_at: now() })
    return { ok: true, state: body.state === 'cleared' ? null : body.state }
  }
  if (method === 'GET' && path === '/profile') return profile()
  if (method === 'PUT' && path === '/profile') {
    for (const k of ['display_name', 'favorite_activity', 'large_text', 'remember_journal']) {
      if (body[k] !== undefined && body[k] !== null) state.prefs[k] = typeof body[k] === 'string' ? body[k].trim() : body[k]
    }
    return profile()
  }
  if (method === 'GET' && path.startsWith('/journal/context')) {
    const m2 = path.match(/session_id=(\d+)/)
    return { context: context(m2 ? Number(m2[1]) : null) }
  }
  if (method === 'POST' && path === '/dev/seed-demo') { seed(); return { ok: true } }
  if (method === 'GET' && path === '/prefs') return { remember_journal: state.prefs.remember_journal }
  if (method === 'PUT' && path === '/prefs') { state.prefs.remember_journal = body.remember_journal; return { ok: true } }
  if (method === 'POST' && path === '/dev/llm-mode') { state.mode = body.mode === 'fail' ? 'fail' : 'mock'; return { mode: state.mode } }
  throw new Error(`demo: no route ${method} ${path}`)
}
