<script setup>
const emit = defineEmits(['go'])
</script>

<template>
  <!-- R3: stopping costs nothing. No "quit", "fail", or "incomplete". -->
  <section class="stack" data-testid="stopped">
    <h2>You stopped. That's fine.</h2>
    <p class="muted">Nothing is lost. You can come back whenever you want.</p>
    <button class="btn btn-primary" data-testid="back-home" @click="emit('go', 'home')">Back to home</button>
  </section>
</template>
