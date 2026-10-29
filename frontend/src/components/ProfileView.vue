<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { api, IS_DEMO } from '../lib/api.js'

const emit = defineEmits(['go'])
const { state: profile, updateProfile, reload } = inject('profile')

const name = ref('')
const activity = ref('')
const savedNote = ref('')
const context = ref('')
const showContext = ref(false)
const seeding = ref(false)

const NAMES = { breath: 'Breath reset', ground: 'Ground reset' }
const SENSING = { none: 'Just the circle', mic: 'Microphone', hold: 'Press and hold' }
const CHECK = { wound_up: 'Wound up', scattered: 'Scattered', low: 'Low', okay: 'Okay' }

onMounted(async () => {
  await reload()
  name.value = profile.display_name || ''
  activity.value = profile.favorite_activity || ''
})

const since = computed(() => {
  if (!profile.first_seen) return 'No visits saved yet'
  return new Date(profile.first_seen).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
})

async function save() {
  await updateProfile({ display_name: name.value, favorite_activity: activity.value })
  savedNote.value = 'Saved.'
  setTimeout(() => (savedNote.value = ''), 2000)
}

async function toggle(key) {
  await updateProfile({ [key]: !profile[key] })
}

async function loadContext() {
  showContext.value = !showContext.value
  if (showContext.value) {
    try { context.value = (await api.journalContext()).context } catch { context.value = 'Not available right now.' }
  }
}

async function seed() {
  seeding.value = true
  try { await api.seedDemo() } catch { /* dev endpoint off */ }
  await reload()
  name.value = profile.display_name || ''
  activity.value = profile.favorite_activity || ''
  seeding.value = false
}

function when(iso) {
  return new Date(iso).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })
}
</script>

<template>
  <section class="stack" data-testid="profile">
    <h2>You</h2>
    <p class="muted small">
      Everything Reset keeps about you is on this page. All of it is optional, and nothing here leaves
      this app except what the journaling companion is told (shown below).
    </p>

    <h3>What you told the app</h3>
    <label class="field">
      <span>What should the app call you?</span>
      <input id="profile-name" v-model="name" maxlength="40" placeholder="Optional" data-testid="profile-name" />
    </label>
    <label class="field">
      <span>Something you enjoy (the companion may mention it)</span>
      <input id="profile-activity" v-model="activity" maxlength="60" placeholder="Optional, for example running"
        data-testid="profile-activity" />
    </label>
    <div class="row">
      <button class="btn-quiet" data-testid="profile-save" @click="save">Save</button>
      <span class="small muted" aria-live="polite">{{ savedNote }}</span>
    </div>

    <h3>What the app learned from what you did</h3>
    <dl class="facts" data-testid="profile-facts">
      <div><dt>Your usual reset</dt><dd>{{ NAMES[profile.usual] || 'Not yet. It appears after you finish one.' }}</dd></div>
      <div><dt>Resets finished</dt><dd>
        {{ profile.resets_completed || 0 }}
        <span v-if="profile.completed_by_skill" class="muted small">
          (Breath {{ profile.completed_by_skill.breath || 0 }}, Ground {{ profile.completed_by_skill.ground || 0 }})
        </span>
      </dd></div>
      <div><dt>Resets you stopped early</dt><dd>{{ profile.resets_stopped || 0 }} <span class="muted small">(that's fine)</span></dd></div>
      <div><dt>Breath follow-along last used</dt><dd>{{ SENSING[profile.last_sensing] || 'Just the circle' }}</dd></div>
      <div><dt>Journal entries</dt><dd>{{ profile.journal_entries || 0 }}</dd></div>
      <div><dt>Check-in right now</dt><dd>{{ CHECK[profile.checkin] || 'None' }}</dd></div>
      <div v-if="profile.recent_checkins?.length"><dt>Recent check-ins</dt><dd class="small">
        <span v-for="(c, i) in profile.recent_checkins" :key="i">{{ CHECK[c.state] }} ({{ when(c.created_at) }})<span v-if="i < profile.recent_checkins.length - 1">, </span></span>
      </dd></div>
      <div><dt>First visit</dt><dd>{{ since }}</dd></div>
    </dl>

    <h3>Settings</h3>
    <label class="toggle">
      <input type="checkbox" :checked="profile.large_text" @change="toggle('large_text')" data-testid="large-text" />
      Larger text
    </label>
    <label class="toggle">
      <input type="checkbox" :checked="profile.remember_journal" @change="toggle('remember_journal')" />
      Let the companion see my past journal entries
    </label>

    <button class="link" data-testid="show-context" @click="loadContext">
      {{ showContext ? 'Hide' : 'See' }} exactly what the journaling companion is told about me
    </button>
    <pre v-if="showContext" class="context" data-testid="context">{{ context }}</pre>

    <p class="small muted">To delete your saved resets and journal entries, use Clear history on the History page.</p>

    <details class="dev small muted">
      <summary>Prototype tools</summary>
      <p>Loads a made-up user, "Sofia", with a week of example resets, check-ins, and a journal entry. It replaces what's saved now.</p>
      <button class="btn-quiet" data-testid="seed-demo" :disabled="seeding" @click="seed">Load example user</button>
      <span v-if="IS_DEMO"> (preview)</span>
    </details>

    <button class="btn" @click="emit('go', 'home')">Back to home</button>
  </section>
</template>

<style scoped>
h3 { font-size: 1rem; margin: 24px 0 4px !important; }
.field { display: flex; flex-direction: column; gap: 4px; }
.field span { font-size: 0.9rem; color: var(--ink-soft); }
input:not([type]) , input[maxlength] {
  font: inherit;
  color: inherit;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 10px 12px;
  min-height: 44px;
}
.row { display: flex; align-items: center; gap: 12px; }
.facts { margin: 0; }
.facts div { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr); gap: 12px; padding: 8px 0; border-top: 1px solid var(--line); }
.facts dt { color: var(--ink-soft); font-size: 0.92rem; }
.facts dd { margin: 0; }
.toggle { display: flex; gap: 10px; align-items: center; min-height: 44px; }
.toggle input { accent-color: var(--accent); width: 20px; height: 20px; }
.context {
  white-space: pre-wrap;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 12px;
  font-size: 0.85rem;
  margin: 0;
  overflow-x: auto;
}
.dev { margin-top: 24px !important; border-top: 1px solid var(--line); padding-top: 12px; }
</style>
