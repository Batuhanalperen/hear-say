<script setup lang="ts">
/**
 * WaveformPlayer — wavesurfer.js wrapper used in the debug audio section.
 *
 * The canvas waveform doubles as a click-to-seek progress bar. Colors are
 * pulled from CSS custom properties so the player follows the active theme.
 */
import WaveSurfer from "wavesurfer.js";

const props = defineProps<{
  src: string;
  label: string;
  icon?: string;
  downloadUrl?: string;
  downloadName?: string;
}>();

const containerRef = ref<HTMLDivElement | null>(null);
const isReady = ref(false);
const isPlaying = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const loading = ref(true);
const error = ref<string | null>(null);

let ws: WaveSurfer | null = null;

function readColor(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
  return value || fallback;
}

function themePalette() {
  return {
    waveColor: readColor("--text-dim", "#71717a"),
    progressColor: readColor("--accent", "#38bdf8"),
    cursorColor: readColor("--accent", "#38bdf8"),
  };
}

function formatTime(t: number): string {
  if (!Number.isFinite(t)) return "0:00";
  const m = Math.floor(t / 60);
  const s = Math.floor(t % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function init() {
  if (!containerRef.value) return;
  loading.value = true;
  error.value = null;

  const palette = themePalette();

  try {
    ws = WaveSurfer.create({
      container: containerRef.value,
      height: 48,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      normalize: true,
      cursorWidth: 1,
      waveColor: palette.waveColor,
      progressColor: palette.progressColor,
      cursorColor: palette.cursorColor,
      url: props.src,
    });

    ws.on("ready", (d) => {
      duration.value = d;
      isReady.value = true;
      loading.value = false;
    });
    ws.on("timeupdate", (t) => {
      currentTime.value = t;
    });
    ws.on("play", () => (isPlaying.value = true));
    ws.on("pause", () => (isPlaying.value = false));
    ws.on("finish", () => {
      isPlaying.value = false;
      currentTime.value = 0;
    });
    ws.on("error", (err) => {
      console.error("WaveformPlayer error:", err);
      error.value = String(err);
      loading.value = false;
    });
  } catch (err) {
    console.error("WaveformPlayer init error:", err);
    error.value = (err as Error).message;
    loading.value = false;
  }
}

function destroy() {
  if (ws) {
    try {
      ws.destroy();
    } catch {
      // ignore
    }
    ws = null;
  }
}

function togglePlay() {
  if (!ws || !isReady.value) return;
  ws.playPause();
}

// Refresh colors when the theme changes
const themeMode = useTheme();
watch(
  () => themeMode.value,
  () => {
    if (!ws) return;
    const palette = themePalette();
    try {
      ws.setOptions({
        waveColor: palette.waveColor,
        progressColor: palette.progressColor,
        cursorColor: palette.cursorColor,
      });
    } catch {
      // older versions may not support setOptions for all fields; ignore
    }
  },
);

onMounted(() => {
  init();
});

onUnmounted(() => {
  destroy();
});

// If the src changes (rare), reinit
watch(
  () => props.src,
  () => {
    destroy();
    nextTick(() => init());
  },
);
</script>

<template>
  <div class="wf">
    <div class="wf-head">
      <div class="wf-label">
        <div v-if="icon" :class="`i-tabler-${icon}`" class="wf-icon" />
        <span>{{ label }}</span>
      </div>
      <div class="wf-meta">
        <span v-if="loading" class="wf-status">Loading…</span>
        <span v-else-if="error" class="wf-status error">Error</span>
        <span v-else class="wf-time">
          {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
        </span>
      </div>
    </div>

    <div class="wf-body">
      <button
        type="button"
        class="wf-play"
        :disabled="!isReady || !!error"
        :aria-label="isPlaying ? 'Pause' : 'Play'"
        @click="togglePlay"
      >
        <div v-if="loading" class="i-tabler-loader-2 animate-spin" />
        <div
          v-else-if="isPlaying"
          class="i-tabler-player-pause-filled"
        />
        <div v-else class="i-tabler-player-play-filled" />
      </button>

      <div ref="containerRef" class="wf-canvas" />

      <a
        v-if="downloadUrl"
        :href="downloadUrl"
        :download="downloadName"
        class="wf-download"
        title="Download"
      >
        <div class="i-tabler-download" />
      </a>
    </div>

    <div v-if="error" class="wf-error-text">{{ error }}</div>
  </div>
</template>

<style scoped>
.wf {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--bg-sunken);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
}

.wf-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  min-height: 20px;
}

.wf-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text);
}

.wf-icon {
  color: var(--accent);
  font-size: 16px;
}

.wf-meta {
  font-size: var(--text-xs);
  font-family: "JetBrains Mono", monospace;
  color: var(--text-dim);
}

.wf-meta .error {
  color: var(--danger);
}

.wf-body {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.wf-play {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  min-width: 36px;
  border-radius: var(--radius-full);
  background: var(--accent);
  color: var(--accent-contrast);
  border: none;
  font-size: 16px;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.wf-play:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: scale(1.04);
}

.wf-play:disabled {
  background: var(--border-strong);
  color: var(--text-dim);
  cursor: not-allowed;
}

.wf-canvas {
  flex: 1;
  min-width: 0;
  /* wavesurfer renders into this div */
}

.wf-download {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  color: var(--text-dim);
  border: 1px solid transparent;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.wf-download:hover {
  color: var(--text);
  background: var(--bg-raised);
  border-color: var(--border);
}

.wf-error-text {
  font-size: var(--text-xs);
  color: var(--danger);
}
</style>
