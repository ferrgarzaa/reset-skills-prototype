<script setup>
// Static content only. No network call, no model, no classifier.
// It must work with the backend stopped.
defineEmits(['close'])
</script>

<template>
  <div class="overlay" role="dialog" aria-modal="true" aria-labelledby="crisis-title" data-testid="crisis-panel">
    <div class="panel">
      <h2 id="crisis-title">Need help now</h2>
      <p class="muted">If you're in danger or thinking about hurting yourself, please reach out to a person now.</p>
      <ul>
        <li>
          <strong>988 Suicide &amp; Crisis Lifeline</strong><br />
          Call or text <a href="tel:988">988</a> (US, 24/7)
        </li>
        <li>
          <strong>Crisis Text Line</strong><br />
          Text <a href="sms:741741?&body=HOME">HOME to 741741</a> (US, 24/7)
        </li>
        <li>
          <strong>Emergency</strong><br />
          Call <a href="tel:911">911</a>
        </li>
      </ul>
      <p class="small muted">This is a class prototype. It can't help in an emergency.</p>
      <button class="btn btn-primary" @click="$emit('close')" autofocus>Close</button>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(20, 24, 26, 0.45);
  display: grid;
  place-items: center;
  padding: 16px;
  z-index: 50;
}
.panel {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 24px;
  width: min(440px, 100%);
}
ul { list-style: none; padding: 0; margin: 16px 0; }
li { padding: 12px 0; border-top: 1px solid var(--line); }
li:last-child { border-bottom: 1px solid var(--line); }
a { color: var(--help); font-weight: 600; }
</style>
