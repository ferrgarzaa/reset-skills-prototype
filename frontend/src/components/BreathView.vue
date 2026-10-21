<script setup>
import { ref, computed, onBeforeUnmount, watch } from 'vue'
import { api, FALLBACK_STEPS } from '../lib/api.js'
import { BreathSensor } from '../lib/breathSensor.js'

const props = defineProps({
  fromUsual: { type: Boolean, default: false },
  defaultSensing: { type: String, default: 'none' },
  paused: { type: Boolean, default: false },
})
const emit = defineEmits(['go'])

// ---- setup (entry time, measured separately) ----
const stage = ref('setup') // setup | running
const sensing = ref(['mic', 'hold', 'none'].includes(props.defaultSensing) ? props.defaultSensing : 'none')
const setupNote = ref('')
const starting = ref(false)

// ---- exercise state ----
const sessionId = ref(null)
const saved = ref(true)
let steps = FALLBACK_STEPS.breath
let timeline = []
let total = 0
let raf = 0
let lastTs = 0
let t0 = 0
const elapsed = ref(0)
let pausedMs = 0
const phaseLog = []
let lastPhaseKey = ''
let sensor = null

// per-cycle sensing
const heard = ref([]) // booleans per cycle
let exhaleMs = 0
let holdInMs = 0
let releaseOutMs = 0
const holding = ref(false)
const ring = ref(0) // 0..1 for mic feedback

function buildTimeline() {
  timeline = []
  let at = 0
  for (const s of steps) {
    if (s.kind === 'cycle') {
      const inhale = (s.duration_s * 1000 * 4) / 10
      const exhale = s.duration_s * 1000 - inhale
      const cycle = timeline.filter((p) => p.type === 'in').length
      timeline.push({ type: 'in', start: at, ms: inhale, cycle, text: 'Breathe in' })
      at += inhale
      timeline.push({ type: 'out', start: at, ms: exhale, cycle, text: 'Breathe out' })
      at += exhale
    } else {
      timeline.push({ type: s.kind, start: at, ms: s.duration_s * 1000, text: s.text })
      at += s.duration_s * 1000
    }
  }
  total = at
  heard.value = Array(timeline.filter((p) => p.type === 'in').length).fill(false)
}

const phase = computed(() => {
  const e = elapsed.value
  return timeline.find((p) => e >= p.start && e < p.start + p.ms) || timeline[timeline.length - 1]
})
const remaining = computed(() =>
  phase.value ? Math.ceil((phase.value.start + phase.value.ms - elapsed.value) / 1000) : 0)
const progress = computed(() =>
  phase.value ? Math.min(1, (elapsed.value - phase.value.start) / phase.value.ms) : 0)
const ease = (x) => 0.5 - Math.cos(Math.PI * x) / 2
const scale = computed(() => {
  const p = phase.value
  if (!p) return 0.55
  if (p.type === 'in') return 0.55 + 0.45 * ease(progress.value)
  if (p.type === 'out') return 1 - 0.45 * ease(progress.value)
  return 0.55
})
const cycleCount = computed(() => heard.value.length)
const currentCycle = computed(() => phase.value?.cycle ?? -1)
const cueText = computed(() => {
  const p = phase.value
  if (!p) return ''
  if (p.type === 'in' || p.type === 'out') return `${p.text}  ${remaining.value}`
  return p.text
})
const heardNow = computed(() => currentCycle.value >= 0 && heard.value[currentCycle.value])

async function begin() {
  starting.value = true
  setupNote.value = ''
  if (sensing.value === 'mic') {
    try {
      sensor = new BreathSensor()
      await sensor.start()
    } catch {
      sensor = null
      sensing.value = 'hold'
      setupNote.value = "Couldn't use the microphone, so you can press and hold the circle instead."
      starting.value = false
      return
    }
  }
  try {
    const r = await api.startSession('breath', sensing.value, props.fromUsual)
    sessionId.value = r.session_id
    steps = r.steps
  } catch {
    saved.value = false // backend down: run anyway with built-in steps
  }
  buildTimeline()
  stage.value = 'running'
  starting.value = false
  t0 = performance.now()
  lastTs = t0
  raf = requestAnimationFrame(tick)
}

function tick(ts) {
  const dt = Math.max(0, ts - lastTs) // rAF timestamps can be slightly before t0
  lastTs = ts
  if (props.paused) {
    pausedMs += dt
  } else {
    elapsed.value += dt
    track(dt)
  }
  const key = `${phase.value.type}-${phase.value.cycle ?? ''}`
  if (key !== lastPhaseKey) {
    phaseLog.push({ phase: key, at_ms: Math.round(ts - t0) })
    lastPhaseKey = key
  }
  if (elapsed.value >= total) {
    finish('completed')
    return
  }
  raf = requestAnimationFrame(tick)
}

let trackedType = ''
function track(dt) {
  const p = phase.value
  const newInhale = p.type === 'in' && trackedType !== 'in'
  trackedType = p.type
  if (newInhale) { exhaleMs = 0; holdInMs = 0; releaseOutMs = 0 }
  if (sensing.value === 'mic' && sensor) {
    ring.value = sensor.intensity()
    if (p.type === 'intro') sensor.calibrateSample()
    else if (sensor.floor === null) sensor.finishCalibration()
    if (p.type === 'out' && sensor.isBreathing()) {
      exhaleMs += dt
      if (exhaleMs >= 600) heard.value[p.cycle] = true
    }
  } else if (sensing.value === 'hold') {
    if (p.type === 'in' && holding.value) holdInMs += dt
    if (p.type === 'out' && !holding.value) {
      releaseOutMs += dt
      if (holdInMs >= 1500 && releaseOutMs >= 1500) heard.value[p.cycle] = true
    }
  }
}

function stepsCompleted() {
  // intro = 1 step, each full cycle = 1 step, close = 1 step
  const e = elapsed.value
  let n = 0
  for (const s of timeline) {
    if (s.type === 'in') continue
    if (e >= s.start + s.ms) n++
  }
  return n
}

let finished = false
async function finish(status) {
  if (finished) return
  finished = true
  cancelAnimationFrame(raf)
  sensor?.stop()
  const end = performance.now()
  const data = {
    status,
    steps_completed: status === 'completed' ? steps.length : stepsCompleted(),
    duration_s: Math.round(elapsed.value) / 1000,
    breaths_detected: sensing.value === 'none' ? null : heard.value.filter(Boolean).length,
    timing: {
      wall_ms: Math.round(end - t0),
      active_ms: Math.round(elapsed.value),
      paused_ms: Math.round(pausedMs),
      planned_ms: total,
      phases: phaseLog,
    },
  }
  console.info('[Reset] breath timing', JSON.stringify(data.timing))
  if (sessionId.value) {
    try { await api.finishSession(sessionId.value, data) } catch { saved.value = false }
  }
  if (status === 'completed') emit('go', 'done', { sessionId: sessionId.value, skill: 'breath', saved: saved.value })
  else emit('go', 'stopped')
}

watch(() => props.paused, (p) => { if (p) holding.value = false })

onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  sensor?.stop()
})

const holdStart = () => { if (sensing.value === 'hold') holding.value = true }
const holdEnd = () => { holding.value = false }
</script>

<template>
  <!-- Setup: entry time, reported separately from the exercise. -->
  <section v-if="stage === 'setup'" class="stack" data-testid="breath-setup">
    <h2>Breath reset</h2>
    <p class="muted">About 1 minute. A circle shows the pace: in for 4, out for 6.</p>

    <fieldset class="sense">
      <legend class="small muted">Follow along with</legend>
      <label :class="{ on: sensing === 'none' }"><input type="radio" value="none" v-model="sensing" /> Just the circle</label>
      <label :class="{ on: sensing === 'mic' }"><input type="radio" value="mic" v-model="sensing" data-testid="sense-mic" /> Microphone</label>
      <label :class="{ on: sensing === 'hold' }"><input type="radio" value="hold" v-model="sensing" data-testid="sense-hold" /> Press and hold</label>
    </fieldset>
    <p v-if="sensing === 'mic'" class="small muted">
      The circle gently shows when it hears your breath out. Sound is only checked inside this browser.
      Nothing is recorded or saved.
    </p>
    <p v-if="sensing === 'hold'" class="small muted">
      Hold the circle while you breathe in, and let go while you breathe out.
    </p>
    <p v-if="setupNote" class="small note" data-testid="setup-note">{{ setupNote }}</p>

    <button class="btn btn-primary" data-testid="begin" :disabled="starting" @click="begin">Start</button>
    <button class="link" @click="emit('go', 'home')">Back</button>
  </section>

  <!-- Exercise: one action per screen (D2). Only the cue, Stop, and Need help now. -->
  <section v-else class="run" data-testid="breath-run">
    <div
      class="circle-wrap"
      :class="{ hold: sensing === 'hold' }"
      role="img"
      :aria-label="cueText"
      @pointerdown.prevent="holdStart"
      @pointerup="holdEnd"
      @pointerleave="holdEnd"
      @pointercancel="holdEnd"
    >
      <div class="ring" :style="{ transform: `scale(${scale * 1.12})`, opacity: sensing === 'mic' ? ring * 0.8 : 0 }"></div>
      <div class="circle" :class="{ holding, heard: heardNow }" :style="{ transform: `scale(${scale})` }"></div>
    </div>

    <p class="cue" aria-live="polite" data-testid="cue">{{ cueText }}</p>
    <p class="sub small muted">
      <span v-if="currentCycle >= 0">Breath {{ currentCycle + 1 }} of {{ cycleCount }}</span>
      <span v-if="sensing !== 'none' && heardNow" class="heard-tag" data-testid="heard"> · with you</span>
      <span v-if="paused"> · paused</span>
    </p>
    <p v-if="!saved" class="small muted">Not being saved right now.</p>

    <button class="btn-quiet stop" data-testid="stop" @click="finish('stopped')">Stop</button>
  </section>
</template>

<style scoped>
.sense { border: 1px solid var(--line); border-radius: var(--radius); padding: 8px 12px 12px; margin: 16px 0 0; }
.sense label { display: block; padding: 10px 8px; border-radius: 10px; cursor: pointer; }
.sense label.on { background: var(--accent-soft); }
.sense input { margin-right: 8px; accent-color: var(--accent); }
.note { color: var(--help); }

.run { display: flex; flex-direction: column; align-items: center; text-align: center; padding-top: 24px; }
.circle-wrap {
  position: relative;
  width: min(280px, 72vw);
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  touch-action: none;
  user-select: none;
}
.circle-wrap.hold { cursor: pointer; }
.circle, .ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
}
.circle {
  background: var(--accent-soft);
  border: 2px solid var(--accent);
  transition: background-color 0.4s, border-color 0.4s;
}
.circle.holding { background: var(--accent); }
.circle.heard { border-color: var(--ink-soft); }
.ring { border: 6px solid var(--accent); transition: opacity 0.15s; }
.cue { font-size: 1.4rem; margin: 28px 0 4px; min-height: 1.6em; white-space: pre; }
.sub { min-height: 1.4em; margin: 0 0 24px; }
.heard-tag { color: var(--accent); font-weight: 600; }
.stop { margin-top: 12px; }
</style>
