<script setup>
import { ref, nextTick, onMounted, inject } from 'vue'
import { api } from '../lib/api.js'
import { crisisMatch } from '../lib/crisis.js'

const emit = defineEmits(['go'])
const crisis = inject('crisis')

const STARTERS = [
  "What's taking up the most space in my head",
  'Something that went okay today',
  "Something I'm carrying",
]

const sessionId = ref(null)
const messages = ref([]) // {role, content, source}
const draft = ref('')
const sending = ref(false)
const remember = ref(true)
const listEl = ref(null)

onMounted(async () => {
  try { remember.value = (await api.prefs()).remember_journal } catch { /* keep default */ }
})

async function scrollDown() {
  await nextTick()
  listEl.value?.lastElementChild?.scrollIntoView({ block: 'end', behavior: 'smooth' })
}

function useStarter(s) {
  draft.value = s + ': '
  document.getElementById('journal-input')?.focus()
}

async function send() {
  const text = draft.value.trim()
  if (!text || sending.value) return
  // Open the crisis panel immediately, before any network call (works even if backend is down).
  if (crisisMatch(text)) crisis.open()
  messages.value.push({ role: 'user', content: text })
  draft.value = ''
  sending.value = true
  scrollDown()
  try {
    const r = await api.journalMessage(sessionId.value, text)
    sessionId.value = r.session_id
    messages.value.push({ role: 'assistant', content: r.reply, source: r.source })
    if (r.crisis) crisis.open()
  } catch {
    messages.value.push({
      role: 'assistant',
      source: 'offline',
      content: "The app can't reach its server right now, so this wasn't saved. You can try again in a moment, or take a Breath reset.",
    })
  } finally {
    sending.value = false
    scrollDown()
  }
}

function onKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
}

async function toggleRemember() {
  remember.value = !remember.value
  try { await api.setPrefs({ remember_journal: remember.value }) } catch { /* ignore */ }
}

async function done() {
  if (sessionId.value) { try { await api.journalEnd(sessionId.value) } catch { /* ignore */ } }
  emit('go', 'home')
}
</script>

<template>
  <section class="journal" data-testid="journal">
    <h2>Journal</h2>
    <p class="small muted">
      A place to write things out. A journaling companion replies briefly. It's not a therapist,
      and nobody else reads this.
    </p>

    <div v-if="!messages.length" class="starters">
      <p class="small muted">Not sure where to start? Optional:</p>
      <button v-for="s in STARTERS" :key="s" class="btn-quiet chip" @click="useStarter(s)">{{ s }}</button>
    </div>

    <div class="msgs" ref="listEl" aria-live="polite">
      <div v-for="(m, i) in messages" :key="i" :class="['msg', m.role]" :data-source="m.source"
        data-testid="journal-msg">{{ m.content }}</div>
      <div v-if="sending" class="msg assistant typing">…</div>
    </div>

    <div class="composer">
      <textarea id="journal-input" v-model="draft" rows="3" data-testid="journal-input"
        placeholder="Write as much or as little as you want" @keydown="onKey"></textarea>
      <button class="btn btn-primary send" data-testid="journal-send" :disabled="!draft.trim() || sending"
        @click="send">Send</button>
    </div>

    <div class="foot small">
      <label class="muted">
        <input type="checkbox" :checked="remember" @change="toggleRemember" data-testid="remember" />
        Let the companion see my past journal entries
      </label>
      <button class="btn-quiet" data-testid="journal-done" @click="done">I'm done</button>
    </div>
  </section>
</template>

<style scoped>
.starters { margin: 16px 0; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.starters p { width: 100%; margin: 0; }
.chip { font-size: 0.9rem; }
.msgs { display: flex; flex-direction: column; gap: 10px; margin: 16px 0; }
.msg { padding: 12px 14px; border-radius: var(--radius); max-width: 88%; white-space: pre-wrap; }
.msg.user { align-self: flex-end; background: var(--accent-soft); }
.msg.assistant { align-self: flex-start; background: var(--surface); border: 1px solid var(--line); }
.typing { color: var(--ink-soft); }
.composer { display: flex; flex-direction: column; gap: 8px; }
textarea {
  width: 100%;
  font: inherit;
  color: inherit;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 12px;
  resize: vertical;
}
.send { text-align: center; }
.foot { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-top: 16px; flex-wrap: wrap; }
.foot input { accent-color: var(--accent); margin-right: 6px; }
</style>
