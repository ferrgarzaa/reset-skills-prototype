<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../lib/api.js'

const emit = defineEmits(['go'])
const loaded = ref(false)
const offline = ref(false)
const line = ref('Take a short reset. Stop whenever you want.')
const lineSource = ref('static')
const usual = ref(null)
const lastSensing = ref('none')

const NAMES = { breath: 'Breath reset', ground: 'Ground reset' }

onMounted(async () => {
  try {
    const h = await api.home()
    line.value = h.opening_line
    lineSource.value = h.opening_source
    usual.value = h.usual
    lastSensing.value = h.last_sensing || 'none'
  } catch {
    offline.value = true
  } finally {
    loaded.value = true
  }
})

function start(skill, fromUsual = false) {
  emit('go', skill, { fromUsual, defaultSensing: lastSensing.value })
}
</script>

<template>
  <section class="stack">
    <p class="opening" :data-source="lineSource" data-testid="opening-line">{{ line }}</p>

    <button class="btn" data-testid="start-breath" @click="start('breath')">
      Breath reset <span class="meta">about 1 min</span>
    </button>
    <button class="btn" data-testid="start-ground" @click="start('ground')">
      Ground reset <span class="meta">about 1 min</span>
    </button>
    <button v-if="usual" class="btn usual" data-testid="start-usual" @click="start(usual, true)">
      Your usual: {{ NAMES[usual] }}
    </button>

    <div class="divider"></div>

    <button class="btn" data-testid="open-journal" @click="emit('go', 'journal')">
      Journal <span class="meta">write it out</span>
    </button>

    <p class="foot">
      <button class="link" @click="emit('go', 'history')">History</button>
    </p>
    <p v-if="offline" class="small muted" data-testid="offline-note">
      The app can't reach its server right now. The exercises still work, but they won't be saved.
    </p>
    <p class="small muted disclaimer">
      Class prototype for practicing short skills. Not therapy, and nobody monitors what you do here.
    </p>
  </section>
</template>

<style scoped>
.opening { font-size: 1.2rem; margin: 8px 0 24px; min-height: 2.4em; }
.usual { background: var(--accent-soft); border-color: transparent; }
.divider { height: 1px; background: var(--line); margin: 20px 0 !important; }
.foot { margin-top: 20px !important; }
.disclaimer { margin-top: 32px !important; }
</style>
