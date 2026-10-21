<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { api, FALLBACK_STEPS } from '../lib/api.js'

const props = defineProps({
  fromUsual: { type: Boolean, default: false },
  paused: { type: Boolean, default: false },
})
const emit = defineEmits(['go'])

const steps = ref(FALLBACK_STEPS.ground)
const sessionId = ref(null)
const saved = ref(true)
const index = ref(0) // which step is on screen
const taps = ref(0)
const ready = ref(false)

let t0 = 0
let pausedMs = 0
let pauseStart = 0
let introTimer = 0
let advanceTimer = 0
const log = []

const step = computed(() => steps.value[index.value])

onMounted(async () => {
  try {
    const r = await api.startSession('ground', null, props.fromUsual)
    sessionId.value = r.session_id
    steps.value = r.steps
  } catch {
    saved.value = false
  }
  ready.value = true
  t0 = performance.now() // first exercise instruction is now on screen
  log.push({ step: 1, at_ms: 0 })
  scheduleIntro(steps.value[0].duration_s * 1000)
})

function scheduleIntro(ms) {
  const startedAt = performance.now()
  introTimer = setTimeout(() => {
    if (props.paused) return scheduleIntro(300)
    next()
  }, ms)
  return startedAt
}

watch(() => props.paused, (p) => {
  if (p) pauseStart = performance.now()
  else if (pauseStart) { pausedMs += performance.now() - pauseStart; pauseStart = 0 }
})

function tap() {
  if (!step.value || step.value.kind !== 'sense' || props.paused) return
  if (taps.value >= step.value.count) return
  taps.value++
  if (taps.value === step.value.count) advanceTimer = setTimeout(next, 600)
}

function next() {
  clearTimeout(advanceTimer)
  clearTimeout(introTimer)
  if (index.value >= steps.value.length - 1) return finish('completed')
  index.value++
  taps.value = 0
  log.push({ step: index.value + 1, at_ms: Math.round(performance.now() - t0) })
}

let finished = false
async function finish(status) {
  if (finished) return
  finished = true
  clearTimeout(advanceTimer)
  clearTimeout(introTimer)
  const wall = performance.now() - t0
  const active = wall - pausedMs - (pauseStart ? performance.now() - pauseStart : 0)
  const data = {
    status,
    steps_completed: status === 'completed' ? steps.value.length : index.value,
    duration_s: Math.round(active) / 1000,
    timing: { wall_ms: Math.round(wall), active_ms: Math.round(active), paused_ms: Math.round(pausedMs), steps: log },
  }
  console.info('[Reset] ground timing', JSON.stringify(data.timing))
  if (sessionId.value) {
    try { await api.finishSession(sessionId.value, data) } catch { saved.value = false }
  }
  if (status === 'completed') emit('go', 'done', { sessionId: sessionId.value, skill: 'ground', saved: saved.value })
  else emit('go', 'stopped')
}

onBeforeUnmount(() => { clearTimeout(advanceTimer); clearTimeout(introTimer) })
</script>

<template>
  <section v-if="ready && step" class="run" data-testid="ground-run">
    <template v-if="step.kind === 'intro'">
      <p class="cue">{{ step.text }}</p>
      <button class="btn-quiet" @click="next">Begin</button>
    </template>

    <template v-else>
      <p class="cue" data-testid="cue">{{ step.text }}</p>
      <button class="pad" data-testid="ground-pad" @click="tap"
        :aria-label="`Tap when you notice one. ${taps} of ${step.count}`">
        <span class="dots">
          <span v-for="i in step.count" :key="i" class="dot" :class="{ on: i <= taps }"></span>
        </span>
        <span class="small muted">Tap each time you notice one. No need to type it.</span>
      </button>
      <button class="link" data-testid="next-sense" @click="next">
        {{ index === steps.length - 1 ? 'Finish' : 'Next sense' }}
      </button>
    </template>

    <p v-if="!saved" class="small muted">Not being saved right now.</p>
    <button class="btn-quiet stop" data-testid="stop" @click="finish('stopped')">Stop</button>
  </section>
</template>

<style scoped>
.run { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 20px; padding-top: 32px; }
.cue { font-size: 1.35rem; margin: 0; }
.pad {
  width: 100%;
  min-height: 220px;
  border-radius: var(--radius);
  border: 1px solid var(--line);
  background: var(--surface);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  touch-action: manipulation;
}
.dots { display: flex; gap: 14px; }
.dot { width: 22px; height: 22px; border-radius: 50%; border: 2px solid var(--accent); transition: background-color 0.3s; }
.dot.on { background: var(--accent); }
.stop { margin-top: 8px; }
</style>
