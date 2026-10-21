<script setup>
import { ref, onMounted } from 'vue'
import { api, IS_DEMO } from '../lib/api.js'

const emit = defineEmits(['go'])
const items = ref([])
const error = ref(false)
const open = ref(null) // {session, messages}
const confirmClear = ref(false)
const mode = ref('')

const NAMES = { breath: 'Breath reset', ground: 'Ground reset', journal: 'Journal' }

async function load() {
  try {
    items.value = (await api.history()).sessions
    error.value = false
  } catch {
    error.value = true
  }
  try { mode.value = (await api.health()).llm.mode } catch { mode.value = '' }
}
onMounted(load)

function when(iso) {
  const d = new Date(iso)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) + ', ' +
    d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })
}
function length(s) {
  if (s.duration_s == null) return ''
  return s.duration_s < 90 ? `${Math.round(s.duration_s)} sec` : `${Math.round(s.duration_s / 60)} min`
}
function status(s) {
  if (s.kind === 'journal') return ''
  return s.status === 'completed' ? 'Done' : s.status === 'stopped' ? 'Stopped' : 'Not finished'
}

async function view(s) {
  if (s.kind !== 'journal') return
  try { open.value = await api.session(s.id) } catch { error.value = true }
}

async function clearAll() {
  await api.clearHistory()
  confirmClear.value = false
  open.value = null
  load()
}

async function setMode(m) {
  try { mode.value = (await api.setLlmMode(m)).mode } catch { /* dev endpoint off */ }
}
</script>

<template>
  <section class="stack" data-testid="history">
    <template v-if="open">
      <button class="link" @click="open = null">Back to history</button>
      <h2>Journal, {{ when(open.session.started_at) }}</h2>
      <div class="msgs">
        <div v-for="(m, i) in open.messages.filter((x) => x.purpose === 'chat')" :key="i"
          :class="['msg', m.role]">{{ m.content }}</div>
      </div>
    </template>

    <template v-else>
      <h2>History</h2>
      <p v-if="error" class="muted">History can't be loaded right now.</p>
      <p v-else-if="!items.length" class="muted">Nothing here yet.</p>

      <ul class="list" v-else>
        <li v-for="s in items" :key="s.id" data-testid="history-item">
          <button class="row" :class="{ clickable: s.kind === 'journal' }" @click="view(s)">
            <span class="name">{{ NAMES[s.kind] }}</span>
            <span class="meta muted small">{{ when(s.started_at) }}</span>
            <span class="detail small">
              <template v-if="s.kind === 'journal'">{{ (s.first_text || '').slice(0, 70) }}</template>
              <template v-else>{{ status(s) }}<template v-if="length(s)"> · {{ length(s) }}</template></template>
            </span>
          </button>
        </li>
      </ul>

      <div v-if="items.length" class="clear">
        <button v-if="!confirmClear" class="link" data-testid="clear" @click="confirmClear = true">Clear history</button>
        <span v-else class="small">
          Delete everything saved?
          <button class="btn-quiet" data-testid="clear-yes" @click="clearAll">Delete</button>
          <button class="link" @click="confirmClear = false">Keep it</button>
        </span>
      </div>

      <details class="dev small muted">
        <summary>Prototype tools</summary>
        <p>Model mode: <strong data-testid="llm-mode">{{ mode || 'unknown' }}</strong>{{ IS_DEMO ? ' (preview)' : '' }}</p>
        <p>Use "fail" to see what happens when the model doesn't respond.</p>
        <button class="btn-quiet" @click="setMode('mock')">mock</button>
        <button v-if="!IS_DEMO" class="btn-quiet" @click="setMode('live')">live</button>
        <button class="btn-quiet" data-testid="mode-fail" @click="setMode('fail')">fail</button>
      </details>
    </template>

    <button class="btn" @click="emit('go', 'home')">Back to home</button>
  </section>
</template>

<style scoped>
.list { list-style: none; padding: 0; margin: 0; }
.list li + li { border-top: 1px solid var(--line); }
.row {
  width: 100%;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 2px 12px;
  text-align: left;
  background: none;
  border: none;
  padding: 12px 4px;
  cursor: default;
}
.row.clickable { cursor: pointer; }
.row.clickable:hover .name { text-decoration: underline; }
.detail { grid-column: 1 / -1; color: var(--ink-soft); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.clear { margin-top: 16px !important; }
.dev { margin-top: 32px !important; border-top: 1px solid var(--line); padding-top: 12px; }
.dev button { margin-right: 6px; }
.msgs { display: flex; flex-direction: column; gap: 10px; }
.msg { padding: 12px 14px; border-radius: var(--radius); max-width: 88%; white-space: pre-wrap; }
.msg.user { align-self: flex-end; background: var(--accent-soft); }
.msg.assistant { align-self: flex-start; background: var(--surface); border: 1px solid var(--line); }
</style>
