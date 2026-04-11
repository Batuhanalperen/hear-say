<script setup lang="ts">
const steps = [
  {
    icon: "file-music",
    label: "Audio input",
    detail: "MP3 / WAV / FLAC",
  },
  {
    icon: "microphone",
    label: "BS-Roformer",
    detail: "Strip vocals",
  },
  {
    icon: "stack-2",
    label: "Demucs htdemucs_6s",
    detail: "Isolate piano stem",
  },
  {
    icon: "piano",
    label: "ByteDance",
    detail: "Piano transcription",
  },
  {
    icon: "music",
    label: "MIDI + score",
    detail: "Synthesia + sheet",
  },
];
</script>

<template>
  <section class="pipeline">
    <div class="pipeline-header">
      <h2>How it works</h2>
      <p class="pipeline-sub">
        Full-band mode cascades three ML models. Solo mode skips separation and
        goes straight to ByteDance for the cleanest possible result.
      </p>
    </div>
    <div class="flow">
      <template v-for="(step, idx) in steps" :key="step.label">
        <div class="step">
          <div class="step-icon">
            <div :class="`i-tabler-${step.icon}`" />
          </div>
          <div class="step-label">{{ step.label }}</div>
          <div class="step-detail">{{ step.detail }}</div>
        </div>
        <div v-if="idx < steps.length - 1" class="arrow" aria-hidden="true">
          <div class="i-tabler-chevron-right" />
        </div>
      </template>
    </div>
  </section>
</template>

<style scoped>
.pipeline {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  padding: var(--space-10) 0;
}

.pipeline-header {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  max-width: 640px;
}

.pipeline-header h2 {
  font-size: var(--text-2xl);
  font-weight: 700;
  letter-spacing: -0.02em;
  margin: 0;
}

.pipeline-sub {
  font-size: var(--text-base);
  color: var(--text-muted);
  margin: 0;
}

.flow {
  display: flex;
  align-items: stretch;
  gap: var(--space-2);
  overflow-x: auto;
  padding: var(--space-2) 0;
  scrollbar-width: thin;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  padding: var(--space-5) var(--space-4);
  min-width: 140px;
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  text-align: center;
  flex-shrink: 0;
}

.step-icon {
  width: 40px;
  height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: var(--accent-bg);
  color: var(--accent);
  font-size: 20px;
  border: 1px solid var(--accent-border);
  margin-bottom: var(--space-1);
}

.step-label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text);
}

.step-detail {
  font-size: var(--text-xs);
  color: var(--text-dim);
  font-family: "JetBrains Mono", monospace;
}

.arrow {
  display: flex;
  align-items: center;
  color: var(--text-dim);
  font-size: 18px;
  flex-shrink: 0;
}
</style>
