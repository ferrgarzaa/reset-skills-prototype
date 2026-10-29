<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { api } from '../lib/api.js'

const emit = defineEmits(['go'])
const { state: profile, setCheckin } = inject('profile')

const offline = ref(false)
const line = ref('Take a short reset. Stop whenever you want.')
const lineSource = ref('static')
const usual = ref(null)
const lastSensing = ref('none')
const showAll = ref(false)
const picking = ref(false)

const NAMES = { breath: 'Breath reset', ground: 'Ground reset', journal: 'Journal' }

// Optional, one tap, in the person's own words. The app never guesses this.
const CHECKINS = [
  { id: 'wound_up', label: 'Wound up' },
  { id: 'scattered', label: 'Scattered' },
  { id: 'low', label: 'Low' },
  { id: 'okay', label: 'Okay' },
]
const LABEL = Object.fromEntries(CHECKINS.map((c) => [c.id, c.label]))

// How a check-in changes the screen. These are my assumptions, and the
// person can always open every option or change the check-in.
const SUGGEST = { wound_up: 'breath', scattered: 'ground', low: 'journal' }
const WHY = {
  breath: 'A slow breath out is a short, simple place to start. About a minute.',
  ground: 'Noticing things around you, one sense at a time. Taps only, nothing to type.',
  journal: 'A place to put a few words down, if you want. No pressure to write much.',
}

const suggestion = computed(() => SUGGEST[profile.checkin] || null)
// D1: when someone says they're wound up, show less: one suggestion until they ask for more.
const contracted = computed(() => profile.checkin === 'wound_up' && !showAll.value)
const order = computed(() => {
  const base = ['breath', 'ground', 'journal']
  if (!suggestion.value) return base
  return [suggestion.value, ...base.filter((x) => x !== suggestion.value)]
})
const visible = computed(() => (contracted.value ? order.value.slice(0, 1) : order.value))

onMounted(async () => {
  try {
    const h = await api.home()
    line.value = h.opening_line
    lineSource.value = h.opening_source
    usual.value = h.usual
    lastSensing.value = h.last_sensing || 'none'
  } catch {
    offline.value = true
  }
})

function open(kind, fromUsual = false) {
  if (kind === 'journal') return emit('go', 'journal')
  emit('go', kind, { fromUsual, defaultSensing: lastSensing.value })
}

async function choose(id) {
  showAll.value = false
  picking.value = false
  await setCheckin(id)
}
</script>

<template>
  <section class="stack">
    <p v-if="profile.display_name" class="hello" data-testid="hello">Hi, {{ profile.display_name }}.</p>
    <p class="opening" :data-source="lineSource" data-testid="opening-line">{{ line }}</p>

    <!-- Check-in: optional, skippable, changeable. -->
    <div class="checkin" data-testid="checkin">
      <template v-if="!profile.checkin || picking">
        <p class="small muted">How are things right now? Optional, and you can skip it.</p>
        <div class="chips">
          <button v-for="c in CHECKINS" :key="c.id" class="chip" :class="{ on: profile.checkin === c.id }"
            :data-testid="`checkin-${c.id}`" @click="choose(c.id)">{{ c.label }}</button>
        </div>
      </template>
      <p v-else class="small muted" data-testid="checkin-chosen">
        You said: <strong>{{ LABEL[profile.checkin] }}</strong>.
        <button class="link" data-testid="checkin-change" @click="picking = true">Change</button>
        ·
        <button class="link" data-testid="checkin-clear" @click="choose('cleared')">Clear</button>
      </p>
    </div>

    <template v-for="kind in visible" :key="kind">
      <div v-if="kind === suggestion" class="suggested" data-testid="suggested">
        <p class="small label">Suggested for right now</p>
        <button class="btn btn-primary big" :data-testid="`start-${kind}`" @click="open(kind)">
          {{ NAMES[kind] }}<span v-if="kind !== 'journal'" class="meta-light"> · about 1 min</span>
        </button>
        <p class="small muted why">{{ WHY[kind] }}</p>
      </div>
      <button v-else class="btn" :data-testid="kind === 'journal' ? 'open-journal' : `start-${kind}`"
        @click="open(kind)">
        {{ NAMES[kind] }}
        <span class="meta">{{ kind === 'journal' ? 'write it out' : 'about 1 min' }}</span>
      </button>
    </template>

    <button v-if="contracted" class="link" data-testid="show-all" @click="showAll = true">Show all options</button>

    <button v-if="usual && !contracted" class="btn usual" data-testid="start-usual" @click="open(usual, true)">
      Your usual: {{ NAMES[usual] }}
    </button>

    <p class="foot">
      <button class="link" @click="emit('go', 'history')">History</button>
      ·
      <button class="link" data-testid="open-profile" @click="emit('go', 'profile')">You</button>
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
.hello { font-weight: 600; margin: 0; }
.opening { font-size: 1.2rem; margin: 4px 0 16px; min-height: 1.6em; }
.checkin { margin-bottom: 20px !important; }
.checkin p { margin: 0 0 8px; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chip {
  border: 1px solid var(--line);
  background: var(--surface);
  border-radius: 999px;
  padding: 10px 18px;
  min-height: 44px;
}
.chip.on { background: var(--accent-soft); border-color: var(--accent); }
.suggested { display: flex; flex-direction: column; gap: 6px; }
.suggested .label { margin: 0; color: var(--accent); font-weight: 600; letter-spacing: 0.02em; }
.big { padding: 20px 18px; font-size: 1.1rem; }
.meta-light { font-weight: 400; opacity: 0.85; font-size: 0.9rem; }
.why { margin: 2px 0 8px; }
.usual { background: var(--accent-soft); border-color: transparent; }
.foot { margin-top: 20px !important; }
.disclaimer { margin-top: 32px !important; }
</style>
