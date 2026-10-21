<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../lib/api.js'

const props = defineProps({
  sessionId: { type: Number, default: null },
  skill: { type: String, default: 'breath' },
  saved: { type: Boolean, default: true },
})
const emit = defineEmits(['go'])

const FALLBACK = "That's the reset. Take your time."
const line = ref('')
const source = ref('')
const choice = ref(null)

onMounted(async () => {
  if (!props.sessionId) { line.value = FALLBACK; source.value = 'fallback'; return }
  try {
    const r = await api.closing(props.sessionId)
    line.value = r.line
    source.value = r.source
  } catch {
    line.value = FALLBACK
    source.value = 'fallback'
  }
})

async function give(f) {
  choice.value = f
  if (props.sessionId) { try { await api.feedback(props.sessionId, f) } catch { /* optional */ } }
}
</script>

<template>
  <section class="stack" data-testid="done">
    <h2>That's the reset.</h2>
    <p class="line" :data-source="source" data-testid="closing-line">{{ line || ' ' }}</p>

    <div v-if="sessionId" class="fb">
      <p class="small muted">How was it? Optional.</p>
      <div class="row" v-if="!choice">
        <button class="btn-quiet" data-testid="fb-helped" @click="give('helped')">Helped</button>
        <button class="btn-quiet" @click="give('not_sure')">Not sure</button>
        <button class="btn-quiet" @click="give('not_today')">Not today</button>
      </div>
      <p v-else class="small muted">Thanks, noted.</p>
    </div>
    <p v-if="!saved" class="small muted">This one wasn't saved because the app couldn't reach its server.</p>

    <button class="btn btn-primary" data-testid="back-home" @click="emit('go', 'home')">Back to home</button>
    <button class="link" @click="emit('go', 'journal')">Write about it</button>
  </section>
</template>

<style scoped>
.line { font-size: 1.1rem; min-height: 1.6em; }
.row { display: flex; gap: 8px; flex-wrap: wrap; }
.fb { margin: 24px 0 !important; }
</style>
