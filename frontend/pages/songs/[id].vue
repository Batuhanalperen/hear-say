<script setup lang="ts">
const route = useRoute();
const songId = computed(() => Number(route.params.id));

const { data: song, pending, error } = await useSongDetail(songId);

const selectedLevel = ref<string>("raw");
const view = ref<"synthesia" | "sheet">("synthesia");

const availableLevels = computed(() => {
  if (!song.value?.levels) return [];
  return Object.keys(song.value.levels);
});

watchEffect(() => {
  if (song.value?.levels && !song.value.levels[selectedLevel.value]) {
    selectedLevel.value = availableLevels.value[0] ?? "raw";
  }
});

const midiUrl = computed(() =>
  song.value ? levelMidiUrl(song.value.id, selectedLevel.value) : "",
);
const musicXmlUrl = computed(() =>
  song.value ? levelMusicXmlUrl(song.value.id, selectedLevel.value) : "",
);

function formatDuration(seconds: number | null): string {
  if (!seconds) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

const levelLabels: Record<string, string> = {
  raw: "Piano transcription",
  // legacy names for older DB rows
  melody_only: "Melody only",
  melody_plus_chords: "Melody + chords",
  intermediate: "Intermediate",
};

const stemLabelMap: Record<string, string> = {
  // BS-Roformer (cascade step 1)
  bs_roformer_vocals: "BS-Roformer — Vocals (initial separation)",
  bs_roformer_instrumental: "BS-Roformer — Instrumental (fed into Demucs)",
  // Demucs htdemucs_6s (cascade step 2, run on vocal-free instrumental)
  vocals: "Demucs — Vocals (usually empty, BS-Roformer stripped them first)",
  drums: "Demucs — Drums",
  bass: "Demucs — Bass",
  other: "Demucs — Other (synth/pad)",
  piano: "Demucs — Piano ★ (fed into ByteDance)",
  guitar: "Demucs — Guitar",
};

function stemLabel(name: string): string {
  return stemLabelMap[name] ?? name;
}

const stemIconMap: Record<string, string> = {
  bs_roformer_vocals: "microphone-2",
  bs_roformer_instrumental: "music",
  vocals: "microphone",
  drums: "activity",
  bass: "guitar-pick",
  other: "music",
  piano: "piano",
  guitar: "guitar-pick",
};

function stemIcon(name: string): string {
  return stemIconMap[name] ?? "music";
}
</script>

<template>
  <div v-if="pending" class="state-msg">Loading…</div>

  <div v-else-if="error || !song" class="state-msg error">
    <p>Song not found</p>
    <NuxtLink to="/" class="btn-ghost">Back to home</NuxtLink>
  </div>

  <div v-else class="song-detail">
    <!-- Header -->
    <div class="detail-header">
      <NuxtLink to="/" class="back-link">
        <div class="i-tabler-arrow-left" />
        Back
      </NuxtLink>
      <h1 class="song-title-big">{{ song.title }}</h1>
      <div class="song-meta-line">
        <span>{{ song.original_filename }}</span>
        <span class="sep">·</span>
        <span>{{ song.mode }}</span>
        <span class="sep">·</span>
        <span>{{ formatDuration(song.duration_seconds) }}</span>
      </div>
    </div>

    <!-- Level switcher: only shown if the song has more than one level
         (new pipeline produces a single 'raw' level, so this stays hidden) -->
    <div v-if="availableLevels.length > 1" class="card level-switcher-card">
      <div class="level-label">Difficulty level</div>
      <div class="level-buttons">
        <button
          v-for="level in availableLevels"
          :key="level"
          class="level-btn"
          :class="{ active: selectedLevel === level }"
          @click="selectedLevel = level"
        >
          {{ levelLabels[level] ?? level }}
        </button>
      </div>
    </div>

    <!-- View tabs -->
    <div class="view-tabs">
      <button
        v-for="v in ['synthesia', 'sheet'] as const"
        :key="v"
        class="view-tab"
        :class="{ active: view === v }"
        @click="view = v"
      >
        <template v-if="v === 'synthesia'">
          <div class="i-tabler-keyboard" />
          Synthesia
        </template>
        <template v-else>
          <div class="i-tabler-file-music" />
          Sheet music
        </template>
      </button>
    </div>

    <!-- View content -->
    <div class="card view-content">
      <Transition name="fade" mode="out-in">
        <SynthesiaView
          v-if="view === 'synthesia'"
          key="synthesia"
          :midi-url="midiUrl"
        />
        <SheetMusicView
          v-else
          key="sheet"
          :music-xml-url="musicXmlUrl"
          :title="song.title"
        />
      </Transition>
    </div>

    <!-- Downloads -->
    <div class="download-bar">
      <a
        :href="midiUrl"
        class="btn-ghost"
        :download="`${song.title}_${selectedLevel}.mid`"
      >
        <div class="i-tabler-download" />
        Download MIDI
      </a>
      <a
        v-if="song.levels[selectedLevel]?.musicxml"
        :href="musicXmlUrl"
        class="btn-ghost"
        :download="`${song.title}_${selectedLevel}.musicxml`"
      >
        <div class="i-tabler-download" />
        Download MusicXML
      </a>
    </div>

    <!-- Debug: original upload + separation stems -->
    <section class="card stems-section">
      <div class="section-header">
        <h2 class="section-title">
          <div class="i-tabler-bug" />
          Debug — audio files
        </h2>
        <span class="debug-hint">
          {{
            song.stems && song.stems.length > 0
              ? "Listen to each separation stem to assess quality"
              : "Original upload only — solo mode skips source separation"
          }}
        </span>
      </div>
      <div class="stems-grid">
        <!-- Original upload, always shown -->
        <WaveformPlayer
          label="Original upload"
          icon="file-music"
          :src="originalAudioUrl(song.id)"
          :download-url="originalAudioUrl(song.id)"
          :download-name="song.original_filename"
        />

        <!-- Separation stems (full-band mode only) -->
        <WaveformPlayer
          v-for="stem in song.stems"
          :key="stem"
          :label="stemLabel(stem)"
          :icon="stemIcon(stem)"
          :src="stemAudioUrl(song.id, stem)"
          :download-url="stemAudioUrl(song.id, stem)"
          :download-name="`${song.title}_${stem}.wav`"
        />
      </div>
    </section>
  </div>
</template>

<style scoped>
.state-msg {
  text-align: center;
  padding: var(--space-20) var(--space-6);
  color: var(--text-dim);
}

.state-msg.error p {
  color: var(--danger);
  margin-bottom: var(--space-4);
}

.song-detail {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  max-width: 1100px;
  margin: 0 auto;
}

/* Header */
.detail-header {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-sm);
  color: var(--text-muted);
  margin-bottom: var(--space-3);
  width: fit-content;
  transition: color 0.15s ease;
}

.back-link:hover {
  color: var(--accent);
}

.song-title-big {
  font-size: var(--text-3xl);
  font-weight: 700;
  margin: 0;
  letter-spacing: -0.025em;
  line-height: 1.1;
  color: var(--text);
}

.song-meta-line {
  font-size: var(--text-sm);
  color: var(--text-dim);
  display: flex;
  gap: var(--space-2);
  align-items: center;
  flex-wrap: wrap;
  margin-top: var(--space-2);
  font-family: "JetBrains Mono", monospace;
}

.sep {
  color: var(--border-strong);
}

/* Level switcher (only shown when multiple levels exist) */
.level-switcher-card {
  padding: var(--space-4) var(--space-5);
}

.level-label {
  font-size: var(--text-xs);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-3);
  font-weight: 600;
}

.level-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.level-btn {
  padding: 8px 14px;
  font-size: var(--text-sm);
  background: transparent;
  color: var(--text-muted);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-md);
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s ease;
}

.level-btn:hover {
  border-color: var(--text-muted);
  color: var(--text);
}

.level-btn.active {
  background: var(--accent-bg);
  border-color: var(--accent);
  color: var(--accent);
}

/* View tabs */
.view-tabs {
  display: inline-flex;
  gap: var(--space-1);
  padding: 4px;
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  width: fit-content;
}

.view-tab {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 8px 16px;
  background: transparent;
  color: var(--text-muted);
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s ease;
}

.view-tab:hover {
  color: var(--text);
}

.view-tab.active {
  background: var(--accent);
  color: var(--accent-contrast);
  box-shadow: var(--shadow-sm);
}

.view-tab.active:hover {
  color: var(--accent-contrast);
}

.view-content {
  min-height: 500px;
}

/* Download bar */
.download-bar {
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
}

/* Debug stems section */
.stems-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-5);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.section-title > div {
  color: var(--accent);
  font-size: 20px;
}

.debug-hint {
  font-size: var(--text-xs);
  color: var(--text-dim);
  font-style: italic;
  max-width: 420px;
}

.stems-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
</style>
