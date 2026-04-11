<script setup lang="ts">
/**
 * Synthesia-style falling-notes visualisation.
 *
 * Notes fall from the top of the canvas and light up the piano keyboard at
 * the bottom as they hit it. Canvas based. Colors are read from CSS custom
 * properties so the visualisation tracks the active theme.
 */
import { Midi } from "@tonejs/midi";
import * as Tone from "tone";

const props = defineProps<{ midiUrl: string }>();

const midi = shallowRef<Midi | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);
const isPlaying = ref(false);
const playbackTime = ref(0);
const duration = ref(0);

const canvasRef = ref<HTMLCanvasElement | null>(null);

const PIANO_HEIGHT = 90;
const PIXELS_PER_SECOND = 120;
const LOW_PITCH = 21; // A0
const HIGH_PITCH = 108; // C8
const TOTAL_KEYS = HIGH_PITCH - LOW_PITCH + 1;

function isBlackKey(pitch: number): boolean {
  const pc = pitch % 12;
  return [1, 3, 6, 8, 10].includes(pc);
}

// Theme-aware colors. Re-read from CSS custom properties whenever the theme
// changes, cache for draw() so we're not hitting getComputedStyle every frame.
const themeColors = ref({
  bg: "#0a0a0b",
  gridLine: "#18181b",
  gridOctave: "#27272a",
  nowLine: "#38bdf8",
  keyWhite: "#f4f4f5",
  keyWhiteActive: "#38bdf8",
  keyBlack: "#18181b",
  keyBlackActive: "#0284c7",
  noteFalling: "#0284c7",
  noteFallingBlack: "#0369a1",
  noteActive: "#0ea5e9",
  noteActiveBlack: "#7dd3fc",
});

function refreshThemeColors() {
  if (typeof window === "undefined") return;
  const styles = getComputedStyle(document.documentElement);
  const read = (name: string, fallback: string) =>
    styles.getPropertyValue(name).trim() || fallback;

  themeColors.value = {
    bg: read("--bg-base", "#0a0a0b"),
    gridLine: read("--grid-line", "#18181b"),
    gridOctave: read("--grid-octave", "#27272a"),
    nowLine: read("--now-line", "#38bdf8"),
    keyWhite: read("--key-white", "#f4f4f5"),
    keyWhiteActive: read("--key-white-active", "#38bdf8"),
    keyBlack: read("--key-black", "#18181b"),
    keyBlackActive: read("--key-black-active", "#0284c7"),
    noteFalling: read("--note-falling", "#0284c7"),
    noteFallingBlack: read("--note-falling-black", "#0369a1"),
    noteActive: read("--note-active", "#0ea5e9"),
    noteActiveBlack: read("--note-active-black", "#7dd3fc"),
  };
}

// Watch the theme preference so colors follow light/dark switches
const themeMode = useTheme();
watch(
  () => themeMode.value,
  () => {
    refreshThemeColors();
    draw();
  },
);

const { getSampler, isLoading: sampleLoading } = usePianoSampler();
let sampler: Tone.Sampler | null = null;
let scheduledIds: number[] = [];

async function ensureSampler() {
  if (!sampler) {
    sampler = await getSampler();
  }
  return sampler;
}

function scheduleAllNotes() {
  if (!midi.value || !sampler) return;
  clearSchedule();
  const s = sampler;
  for (const track of midi.value.tracks) {
    for (const note of track.notes) {
      const id = Tone.getTransport().schedule((time) => {
        s.triggerAttackRelease(note.name, note.duration, time, note.velocity);
      }, note.time);
      scheduledIds.push(id);
    }
  }
}

function clearSchedule() {
  for (const id of scheduledIds) {
    Tone.getTransport().clear(id);
  }
  scheduledIds = [];
}

async function loadMidi() {
  if (!props.midiUrl) {
    midi.value = null;
    return;
  }
  loading.value = true;
  error.value = null;
  try {
    const res = await fetch(props.midiUrl);
    if (!res.ok) throw new Error(`HTTP ${res.status} — ${res.statusText}`);
    const buffer = await res.arrayBuffer();
    if (buffer.byteLength === 0) {
      throw new Error("Empty MIDI file");
    }
    const parsed = new Midi(buffer);
    if (!parsed.header) {
      throw new Error("MIDI parse failed (no header)");
    }
    midi.value = parsed;
    duration.value = parsed.duration;
  } catch (err) {
    console.error("SynthesiaView loadMidi error:", err);
    error.value = (err as Error).message;
    midi.value = null;
  } finally {
    loading.value = false;
  }
}

function draw() {
  const canvas = canvasRef.value;
  if (!canvas || !midi.value) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const c = themeColors.value;
  const w = canvas.width;
  const h = canvas.height;
  const keyboardTop = h - PIANO_HEIGHT;
  const keyWidth = w / TOTAL_KEYS;

  // Background
  ctx.fillStyle = c.bg;
  ctx.fillRect(0, 0, w, h);

  // Grid lines per white key
  ctx.strokeStyle = c.gridLine;
  ctx.lineWidth = 1;
  for (let i = 0; i < TOTAL_KEYS; i++) {
    const pitch = LOW_PITCH + i;
    if (isBlackKey(pitch)) continue;
    const x = i * keyWidth;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, keyboardTop);
    ctx.stroke();
  }

  // Octave C lines (stronger)
  ctx.strokeStyle = c.gridOctave;
  for (let i = 0; i < TOTAL_KEYS; i++) {
    const pitch = LOW_PITCH + i;
    if (pitch % 12 === 0) {
      const x = i * keyWidth;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, keyboardTop);
      ctx.stroke();
    }
  }

  // "Now" line at the top of the keyboard
  ctx.strokeStyle = c.nowLine;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(0, keyboardTop);
  ctx.lineTo(w, keyboardTop);
  ctx.stroke();

  const visibleSeconds = keyboardTop / PIXELS_PER_SECOND;
  const tMin = playbackTime.value;
  const tMax = playbackTime.value + visibleSeconds;

  const activePitches = new Set<number>();

  for (const track of midi.value.tracks) {
    for (const note of track.notes) {
      const noteEnd = note.time + note.duration;
      if (noteEnd < tMin || note.time > tMax) continue;

      const pitchIdx = note.midi - LOW_PITCH;
      if (pitchIdx < 0 || pitchIdx >= TOTAL_KEYS) continue;

      const x = pitchIdx * keyWidth;
      const yEnd = keyboardTop - (note.time - tMin) * PIXELS_PER_SECOND;
      const yStart = keyboardTop - (noteEnd - tMin) * PIXELS_PER_SECOND;
      const height = yEnd - yStart;

      const active =
        note.time <= playbackTime.value && noteEnd > playbackTime.value;
      if (active) activePitches.add(note.midi);

      ctx.fillStyle = active
        ? isBlackKey(note.midi)
          ? c.noteActiveBlack
          : c.noteActive
        : isBlackKey(note.midi)
          ? c.noteFallingBlack
          : c.noteFalling;

      // Rounded rect
      const r = Math.min(3, Math.max(1, keyWidth * 0.1));
      ctx.beginPath();
      ctx.moveTo(x + r, yStart);
      ctx.lineTo(x + keyWidth - r - 1, yStart);
      ctx.quadraticCurveTo(
        x + keyWidth - 1,
        yStart,
        x + keyWidth - 1,
        yStart + r,
      );
      ctx.lineTo(x + keyWidth - 1, yStart + height - r);
      ctx.quadraticCurveTo(
        x + keyWidth - 1,
        yStart + height,
        x + keyWidth - r - 1,
        yStart + height,
      );
      ctx.lineTo(x + r, yStart + height);
      ctx.quadraticCurveTo(x, yStart + height, x, yStart + height - r);
      ctx.lineTo(x, yStart + r);
      ctx.quadraticCurveTo(x, yStart, x + r, yStart);
      ctx.fill();
    }
  }

  // White keys
  for (let i = 0; i < TOTAL_KEYS; i++) {
    const pitch = LOW_PITCH + i;
    if (isBlackKey(pitch)) continue;
    const x = i * keyWidth;
    const highlighted = activePitches.has(pitch);
    ctx.fillStyle = highlighted ? c.keyWhiteActive : c.keyWhite;
    ctx.fillRect(x, keyboardTop, keyWidth - 0.5, PIANO_HEIGHT);
    ctx.strokeStyle = c.gridLine;
    ctx.lineWidth = 1;
    ctx.strokeRect(x, keyboardTop, keyWidth - 0.5, PIANO_HEIGHT);
  }
  // Black keys on top
  for (let i = 0; i < TOTAL_KEYS; i++) {
    const pitch = LOW_PITCH + i;
    if (!isBlackKey(pitch)) continue;
    const x = i * keyWidth;
    const highlighted = activePitches.has(pitch);
    ctx.fillStyle = highlighted ? c.keyBlackActive : c.keyBlack;
    ctx.fillRect(
      x + keyWidth * 0.15,
      keyboardTop,
      keyWidth * 0.7,
      PIANO_HEIGHT * 0.6,
    );
  }
}

let rafId: number | null = null;
function tick() {
  if (isPlaying.value) {
    playbackTime.value = Tone.getTransport().seconds;
    if (playbackTime.value >= duration.value) {
      stop();
    }
  }
  draw();
  rafId = requestAnimationFrame(tick);
}

async function play() {
  if (!midi.value) return;
  await Tone.start();
  await ensureSampler();
  if (scheduledIds.length === 0) scheduleAllNotes();
  Tone.getTransport().start();
  isPlaying.value = true;
}

function pause() {
  Tone.getTransport().pause();
  isPlaying.value = false;
}

function stop() {
  Tone.getTransport().stop();
  clearSchedule();
  isPlaying.value = false;
  playbackTime.value = 0;
  draw();
}

function togglePlay() {
  if (isPlaying.value) pause();
  else play();
}

function seek(event: Event) {
  const newTime = Number((event.target as HTMLInputElement).value);
  if (Number.isNaN(newTime)) return;
  Tone.getTransport().seconds = newTime;
  playbackTime.value = newTime;
  draw();
}

function resizeCanvas() {
  const canvas = canvasRef.value;
  if (!canvas) return;
  const parent = canvas.parentElement;
  if (!parent) return;
  const rect = parent.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = 520;
  canvas.style.width = `${rect.width}px`;
  canvas.style.height = `520px`;
  draw();
}

onMounted(async () => {
  refreshThemeColors();
  await loadMidi();
  nextTick(() => {
    resizeCanvas();
    rafId = requestAnimationFrame(tick);
  });
  window.addEventListener("resize", resizeCanvas);
});

onUnmounted(() => {
  window.removeEventListener("resize", resizeCanvas);
  if (rafId) cancelAnimationFrame(rafId);
  stop();
  sampler = null;
});

watch(
  () => props.midiUrl,
  async () => {
    stop();
    await loadMidi();
    nextTick(() => resizeCanvas());
  },
);

function formatTime(t: number): string {
  const m = Math.floor(t / 60);
  const s = Math.floor(t % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}
</script>

<template>
  <div class="synthesia">
    <div v-if="loading" class="state-msg">Loading MIDI…</div>
    <div v-else-if="error" class="state-msg error">Error: {{ error }}</div>
    <template v-else-if="midi">
      <div class="player-controls">
        <button
          class="btn btn-primary"
          :disabled="sampleLoading"
          @click="togglePlay"
        >
          <div
            v-if="sampleLoading"
            class="i-tabler-loader-2 animate-spin"
          />
          <div
            v-else
            :class="isPlaying ? 'i-tabler-player-pause-filled' : 'i-tabler-player-play-filled'"
          />
          <span v-if="sampleLoading">Loading piano…</span>
          <span v-else>{{ isPlaying ? "Pause" : "Play" }}</span>
        </button>
        <button class="btn btn-ghost" @click="stop">
          <div class="i-tabler-player-stop-filled" />
          Stop
        </button>
        <div class="time-display">
          <span class="current">{{ formatTime(playbackTime) }}</span>
          <span class="sep">/</span>
          <span class="total">{{ formatTime(duration) }}</span>
        </div>
      </div>

      <div class="canvas-wrap">
        <canvas ref="canvasRef" />
      </div>

      <div class="seek-wrap">
        <input
          type="range"
          class="seek-slider"
          :min="0"
          :max="duration"
          :step="0.05"
          :value="playbackTime"
          @input="seek"
        />
      </div>

      <div class="player-info">
        Notes fall from the top and light up the keyboard as they reach the accent line.
      </div>
    </template>
  </div>
</template>

<style scoped>
.synthesia {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.state-msg {
  text-align: center;
  padding: var(--space-16) var(--space-4);
  color: var(--text-dim);
}
.state-msg.error {
  color: var(--danger);
}

.player-controls {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.time-display {
  font-family: "JetBrains Mono", monospace;
  font-size: var(--text-sm);
  color: var(--text-muted);
  margin-left: auto;
  display: inline-flex;
  gap: 4px;
}
.time-display .current {
  color: var(--text);
}
.time-display .sep {
  color: var(--text-dim);
}

.canvas-wrap {
  position: relative;
  background: var(--bg-base);
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--border);
}
.canvas-wrap canvas {
  display: block;
  width: 100%;
}

.seek-wrap {
  padding: var(--space-1) 0;
}

.seek-slider {
  width: 100%;
  height: 6px;
  appearance: none;
  background: var(--border-strong);
  border-radius: var(--radius-full);
  outline: none;
  cursor: pointer;
  padding: 0;
  border: none;
}
.seek-slider::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
  border: 2px solid var(--bg-base);
  box-shadow: 0 0 0 1px var(--accent);
}
.seek-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
  border: 2px solid var(--bg-base);
}

.player-info {
  font-size: var(--text-xs);
  color: var(--text-dim);
  text-align: center;
}
</style>
