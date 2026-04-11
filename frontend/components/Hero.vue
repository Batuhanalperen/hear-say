<script setup lang="ts">
defineProps<{
  scrollTarget?: string;
}>();

function scrollToTarget(target?: string) {
  if (!target) return;
  const el = document.querySelector(target);
  if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}
</script>

<template>
  <section class="hero">
    <div class="hero-content">
      <div class="hero-eyebrow">
        <span class="dot" />
        Open source · Runs locally on your GPU
      </div>
      <h1 class="hero-title">
        Turn any audio into
        <span class="accent-text">piano sheet music</span>
      </h1>
      <p class="hero-sub">
        Upload an MP3, get back a clean MIDI file, a Synthesia-style falling-notes
        player, a printable score, and grand-piano playback — all powered by
        state-of-the-art source separation and transcription models.
      </p>
      <div class="hero-cta">
        <button class="btn btn-primary" @click="scrollToTarget(scrollTarget)">
          <div class="i-tabler-upload" />
          Upload your first track
        </button>
        <a
          class="btn btn-ghost"
          href="https://github.com/batuhanalperen/hear-say"
          target="_blank"
          rel="noopener noreferrer"
        >
          <div class="i-tabler-brand-github" />
          View on GitHub
        </a>
      </div>
    </div>

    <div class="hero-visual" aria-hidden="true">
      <div class="falling-notes">
        <span
          v-for="(n, i) in 12"
          :key="i"
          class="falling-note"
          :style="{
            left: `${(i * 8.3) + 2}%`,
            animationDelay: `${i * 0.25}s`,
            height: `${30 + ((i * 13) % 40)}px`,
          }"
        />
      </div>
      <div class="visual-keyboard">
        <span v-for="i in 14" :key="`w${i}`" class="vk-white" />
        <span v-for="i in [0, 1, 3, 4, 5, 7, 8, 10, 11, 12]" :key="`b${i}`" class="vk-black" :style="{ left: `calc(${i} * (100% / 14) + (100% / 14) * 0.7)` }" />
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-10);
  padding: var(--space-12) 0 var(--space-16);
  position: relative;
}

@media (min-width: 900px) {
  .hero {
    grid-template-columns: 1.3fr 1fr;
    align-items: center;
    padding: var(--space-16) 0 var(--space-20);
  }
}

.hero-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  max-width: 640px;
}

.hero-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  font-family: "JetBrains Mono", monospace;
  color: var(--text-muted);
  padding: 6px 12px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border);
  background: var(--bg-raised);
  width: fit-content;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 8px var(--success);
}

.hero-title {
  font-size: var(--text-3xl);
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.03em;
  color: var(--text);
  margin: 0;
}

@media (min-width: 900px) {
  .hero-title {
    font-size: var(--text-4xl);
  }
}

.accent-text {
  color: var(--accent);
  background: linear-gradient(
    120deg,
    var(--accent) 0%,
    var(--accent-hover) 100%
  );
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-sub {
  font-size: var(--text-md);
  color: var(--text-muted);
  line-height: var(--lh-normal);
  max-width: 560px;
}

.hero-cta {
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
  margin-top: var(--space-2);
}

/* Decorative visual — a mini falling-notes preview */
.hero-visual {
  position: relative;
  height: 320px;
  border-radius: var(--radius-xl);
  background: var(--bg-raised);
  border: 1px solid var(--border);
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

.falling-notes {
  position: absolute;
  inset: 0 0 60px 0;
  overflow: hidden;
}

.falling-note {
  position: absolute;
  top: -50px;
  width: calc(100% / 14 * 0.85);
  background: var(--accent);
  border-radius: 3px;
  opacity: 0.75;
  animation: fall 4s linear infinite;
}

@keyframes fall {
  0% {
    transform: translateY(0);
    opacity: 0;
  }
  10% {
    opacity: 0.75;
  }
  90% {
    opacity: 0.75;
  }
  100% {
    transform: translateY(320px);
    opacity: 0;
  }
}

.visual-keyboard {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 60px;
  display: flex;
  background: var(--bg-sunken);
  border-top: 2px solid var(--accent);
}

.vk-white {
  flex: 1;
  background: var(--key-white);
  border-right: 1px solid var(--grid-line);
}

.vk-black {
  position: absolute;
  top: 2px;
  width: calc(100% / 14 * 0.55);
  height: 40px;
  background: var(--key-black);
  border-radius: 0 0 2px 2px;
  pointer-events: none;
}
</style>
