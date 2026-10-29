<script setup>
import { ref, provide, reactive, onMounted } from 'vue'
import { api, IS_DEMO } from './lib/api.js'
import CrisisPanel from './components/CrisisPanel.vue'
import HomeView from './components/HomeView.vue'
import BreathView from './components/BreathView.vue'
import GroundView from './components/GroundView.vue'
import DoneView from './components/DoneView.vue'
import StoppedView from './components/StoppedView.vue'
import JournalView from './components/JournalView.vue'
import HistoryView from './components/HistoryView.vue'
import ProfileView from './components/ProfileView.vue'

const view = ref('home')
const params = ref({})
const crisisOpen = ref(false)

// What the person chose to tell the app. Shared by every screen.
const profile = reactive({ display_name: '', checkin: null, large_text: false, loaded: false })

function applyTextSize() {
  document.documentElement.classList.toggle('large-text', !!profile.large_text)
}

async function loadProfile() {
  try {
    Object.assign(profile, await api.profile(), { loaded: true })
  } catch {
    profile.loaded = true
  }
  applyTextSize()
}

async function setCheckin(state) {
  profile.checkin = state === 'cleared' ? null : state
  try { await api.checkin(state) } catch { /* still applies for this visit */ }
}

async function updateProfile(patch) {
  try {
    Object.assign(profile, await api.setProfile(patch))
  } catch {
    Object.assign(profile, patch)
  }
  applyTextSize()
}

function go(name, p = {}) {
  view.value = name
  params.value = p
  window.scrollTo(0, 0)
  if (name === 'home' || name === 'profile') loadProfile()
}

provide('crisis', { open: () => (crisisOpen.value = true), isOpen: crisisOpen })
provide('profile', { state: profile, setCheckin, updateProfile, reload: loadProfile })

onMounted(loadProfile)
</script>

<template>
  <header class="top">
    <button class="brand" @click="go('home')" :disabled="view === 'breath' || view === 'ground'"
      aria-label="Reset, home">Reset</button>
    <!-- Always visible, same place, every screen (R2, D4). -->
    <button class="help" data-testid="need-help" @click="crisisOpen = true">Need help now</button>
  </header>

  <p v-if="IS_DEMO" class="demo small">Preview: replies are sample text, the microphone is off here, and nothing is saved.</p>
  <main :class="['main', view]">
    <HomeView v-if="view === 'home'" @go="go" />
    <BreathView v-else-if="view === 'breath'" v-bind="params" :paused="crisisOpen" @go="go" />
    <GroundView v-else-if="view === 'ground'" v-bind="params" :paused="crisisOpen" @go="go" />
    <DoneView v-else-if="view === 'done'" v-bind="params" @go="go" />
    <StoppedView v-else-if="view === 'stopped'" @go="go" />
    <JournalView v-else-if="view === 'journal'" v-bind="params" @go="go" />
    <HistoryView v-else-if="view === 'history'" @go="go" />
    <ProfileView v-else-if="view === 'profile'" @go="go" />
  </main>

  <CrisisPanel v-if="crisisOpen" @close="crisisOpen = false" />
</template>

<style scoped>
.top {
  position: sticky;
  top: env(safe-area-inset-top, 0px);
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-block: 12px;
  padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px));
  background: var(--bg);
  border-bottom: 1px solid var(--line);
}
.brand {
  background: none;
  border: none;
  font-weight: 600;
  font-size: 1.05rem;
  letter-spacing: 0.02em;
  padding: 6px 0;
}
.brand:disabled { cursor: default; color: var(--ink); }
.help {
  background: var(--help-soft);
  color: var(--help);
  border: 1px solid var(--help);
  border-radius: 999px;
  padding: 8px 16px;
  font-weight: 600;
  font-size: 0.95rem;
}
.main {
  max-width: 520px;
  margin: 0 auto;
  padding-block: 24px 48px;
  padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px));
}
.demo {
  margin: 0;
  padding: 8px max(16px, env(safe-area-inset-right, 0px)) 8px max(16px, env(safe-area-inset-left, 0px));
  background: var(--accent-soft);
  color: var(--ink);
  text-align: center;
}
</style>
