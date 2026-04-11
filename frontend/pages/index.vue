<script setup lang="ts">
import type { SongSummary } from "~/composables/useSongs";

const { data: songs, refresh } = await useSongList();

const isUploading = ref(false);
const title = ref("");
const mode = ref<"solo" | "full-band">("solo");
const file = ref<File | null>(null);
const uploadError = ref<string | null>(null);

// Auto-poll every 2 s while any upload is still processing
const hasRunning = computed(
  () =>
    songs.value?.some(
      (s: SongSummary) => s.status === "running" || s.status === "pending",
    ) ?? false,
);

useIntervalFn(() => {
  if (hasRunning.value) refresh();
}, 2000);

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  file.value = input.files?.[0] ?? null;
  if (file.value && !title.value) {
    title.value = file.value.name.replace(/\.[^.]+$/, "");
  }
}

async function handleSubmit() {
  if (!file.value) {
    uploadError.value = "Please select an audio file";
    return;
  }
  if (!title.value.trim()) {
    uploadError.value = "Title is required";
    return;
  }

  isUploading.value = true;
  uploadError.value = null;

  try {
    await uploadSong({
      title: title.value.trim(),
      mode: mode.value,
      file: file.value,
    });
    title.value = "";
    file.value = null;
    const input = document.querySelector<HTMLInputElement>(
      'input[type="file"]',
    );
    if (input) input.value = "";
    await refresh();
  } catch (err) {
    uploadError.value = (err as Error).message || "Upload failed";
  } finally {
    isUploading.value = false;
  }
}

async function handleDelete(id: number) {
  if (!confirm("Delete this song?")) return;
  try {
    await deleteSong(id);
    await refresh();
  } catch (err) {
    alert("Delete failed: " + (err as Error).message);
  }
}

function formatDuration(seconds: number | null): string {
  if (!seconds) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}
</script>

<template>
  <div class="home">
    <!-- Hero is always visible -->
    <Hero scroll-target="#upload-section" />

    <!-- Workspace sits high so returning users reach it without scrolling far -->
    <div id="upload-section" class="app-section">
      <div class="app-header">
        <h2 class="app-title">Your workspace</h2>
        <p class="app-sub">
          Drop an audio file on the left, track progress on the right.
        </p>
      </div>

      <div class="app-grid">
        <!-- Upload panel -->
        <section class="card upload-card">
          <div class="card-header">
            <div class="card-icon">
              <div class="i-tabler-upload" />
            </div>
            <div class="card-header-text">
              <h3 class="card-title">New upload</h3>
              <p class="card-sub">MP3, WAV, FLAC, OGG, M4A supported</p>
            </div>
          </div>

          <form class="upload-form" @submit.prevent="handleSubmit">
            <div class="field">
              <label>Title</label>
              <input
                v-model="title"
                type="text"
                placeholder="e.g. Clair de Lune"
              />
            </div>

            <div class="field">
              <label>Mode</label>
              <div class="mode-toggle">
                <button
                  type="button"
                  class="mode-btn"
                  :class="{ active: mode === 'solo' }"
                  @click="mode = 'solo'"
                >
                  <div class="i-tabler-piano" />
                  <div class="mode-text">
                    <span class="mode-title">Solo piano</span>
                    <span class="mode-hint">Clean recordings</span>
                  </div>
                </button>
                <button
                  type="button"
                  class="mode-btn"
                  :class="{ active: mode === 'full-band' }"
                  @click="mode = 'full-band'"
                >
                  <div class="i-tabler-music" />
                  <div class="mode-text">
                    <span class="mode-title">Full band</span>
                    <span class="mode-hint">Pop, rock, orchestral</span>
                  </div>
                </button>
              </div>
            </div>

            <div class="field">
              <label>Audio file</label>
              <input
                type="file"
                accept=".mp3,.wav,.flac,.ogg,.m4a"
                @change="handleFileChange"
              />
            </div>

            <p v-if="uploadError" class="error-msg">{{ uploadError }}</p>

            <button
              type="submit"
              :disabled="isUploading || !file"
              class="btn btn-primary submit-btn"
            >
              <div
                v-if="isUploading"
                class="i-tabler-loader-2 animate-spin"
              />
              <div v-else class="i-tabler-arrow-right" />
              <span v-if="isUploading">Uploading…</span>
              <span v-else>Transcribe</span>
            </button>
          </form>
        </section>

        <!-- History list -->
        <section class="card history-card">
          <div class="card-header">
            <div class="card-icon">
              <div class="i-tabler-list" />
            </div>
            <div class="card-header-text">
              <h3 class="card-title">Transcriptions</h3>
              <p class="card-sub">
                {{ songs?.length ?? 0 }} song{{ (songs?.length ?? 0) === 1 ? "" : "s" }}
                <span v-if="hasRunning" class="polling-dot" title="Auto-refreshing…" />
              </p>
            </div>
            <button class="btn btn-ghost btn-compact" @click="refresh()">
              <div class="i-tabler-refresh" />
              <span>Refresh</span>
            </button>
          </div>

          <EmptyState
            v-if="!songs || songs.length === 0"
            title="No songs yet"
            description="Upload your first track with the form on the left to get started."
            icon="music-off"
          />

          <div v-else class="song-list scrollbar-thin">
            <div v-for="song in songs" :key="song.id" class="song-row">
              <QuickPlayButton
                v-if="song.status === 'completed' && song.has_levels"
                :song-id="song.id"
                :midi-url="levelMidiUrl(song.id, 'raw')"
              />
              <div v-else class="song-status-icon" :class="song.status">
                <div
                  v-if="song.status === 'running' || song.status === 'pending'"
                  class="i-tabler-loader-2 animate-spin"
                />
                <div
                  v-else-if="song.status === 'failed'"
                  class="i-tabler-alert-circle"
                />
                <div v-else class="i-tabler-music" />
              </div>

              <div class="song-info">
                <div class="song-title-row">
                  <NuxtLink
                    :to="song.status === 'completed' ? `/songs/${song.id}` : ''"
                    :class="[
                      'song-title',
                      { clickable: song.status === 'completed' },
                    ]"
                  >
                    {{ song.title }}
                  </NuxtLink>
                  <span class="song-mode-badge">{{ song.mode }}</span>
                </div>
                <div class="song-meta">
                  <span :class="['status-label', song.status]">
                    {{ song.status }}
                  </span>
                  <span v-if="song.current_step">· {{ song.current_step }}</span>
                  <span v-if="song.duration_seconds">
                    · {{ formatDuration(song.duration_seconds) }}
                  </span>
                </div>
                <div
                  v-if="song.status === 'running' || song.status === 'pending'"
                  class="progress-track"
                >
                  <div
                    class="progress-fill"
                    :style="{ width: `${song.progress_pct}%` }"
                  />
                </div>
              </div>

              <button
                class="btn-danger-ghost"
                title="Delete"
                @click="handleDelete(song.id)"
              >
                <div class="i-tabler-trash" />
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>

    <!-- Feature cards + pipeline diagram always visible below the workspace -->
    <section class="features">
      <FeatureCard
        icon="piano"
        title="Solo piano transcription"
        description="ByteDance Piano Transcription — state-of-the-art, Maestro-trained. Around 99% accuracy on clean solo piano recordings."
      />
      <FeatureCard
        icon="stack-2"
        title="Full-band cascade"
        description="BS-Roformer strips vocals, Demucs htdemucs_6s isolates the piano stem, then ByteDance transcribes. Three SOTA models working together."
      />
      <FeatureCard
        icon="device-speaker"
        title="Beautiful playback"
        description="Synthesia-style falling notes, printable A4 sheet music, real Salamander Grand Piano samples, and MIDI / MusicXML / PDF export."
      />
    </section>

    <PipelineDiagram />
  </div>
</template>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  gap: var(--space-10);
}

/* Workspace section */
.app-section {
  scroll-margin-top: 100px;
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.app-header {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  max-width: 640px;
}

.app-title {
  font-size: var(--text-2xl);
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text);
  margin: 0;
}

.app-sub {
  font-size: var(--text-base);
  color: var(--text-muted);
  margin: 0;
}

.app-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-6);
}

@media (min-width: 1000px) {
  .app-grid {
    grid-template-columns: minmax(360px, 1fr) minmax(480px, 1.5fr);
    align-items: start;
  }
}

/* Cards (override global .card display while inheriting background/border) */
.card {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.card-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.card-header-text {
  flex: 1;
  min-width: 0;
}

.card-icon {
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
  flex-shrink: 0;
}

.card-title {
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--text);
  margin: 0;
  line-height: 1.2;
}

.card-sub {
  font-size: var(--text-xs);
  color: var(--text-dim);
  margin: 2px 0 0 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.polling-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 8px var(--accent);
  animation: pulse 1.6s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.6;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.3);
  }
}

.btn-compact {
  padding: 6px 12px;
  font-size: var(--text-sm);
}

/* Upload form */
.upload-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.field label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.mode-toggle {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2);
}

.mode-btn {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--bg-base);
  color: var(--text-muted);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  text-align: left;
  font-family: inherit;
  transition: all 0.15s ease;
}

.mode-btn > div:first-child {
  font-size: 22px;
  color: var(--text-dim);
  flex-shrink: 0;
}

.mode-btn:hover {
  border-color: var(--border-strong);
  color: var(--text);
}

.mode-btn.active {
  background: var(--accent-bg);
  border-color: var(--accent);
  color: var(--accent);
}

.mode-btn.active > div:first-child {
  color: var(--accent);
}

.mode-text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
  min-width: 0;
}

.mode-title {
  font-size: var(--text-sm);
  font-weight: 600;
}

.mode-hint {
  font-size: var(--text-xs);
  color: var(--text-dim);
  margin-top: 2px;
}

.error-msg {
  color: var(--danger);
  font-size: var(--text-sm);
  padding: var(--space-2) var(--space-3);
  background: var(--danger-bg);
  border-radius: var(--radius-sm);
  margin: 0;
}

.submit-btn {
  width: 100%;
  padding: 12px 16px;
}

/* Song list */
.song-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  max-height: 720px;
  overflow-y: auto;
  padding-right: var(--space-1);
}

.song-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-base);
  transition: all 0.15s ease;
}

.song-row:hover {
  border-color: var(--border-strong);
  background: var(--bg-sunken);
}

.song-status-icon {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-strong);
  color: var(--text-dim);
  font-size: 18px;
  flex-shrink: 0;
}

.song-status-icon.running,
.song-status-icon.pending {
  color: var(--accent);
  border-color: var(--accent);
}

.song-status-icon.failed {
  color: var(--danger);
  border-color: var(--danger);
}

.song-info {
  flex: 1;
  min-width: 0;
}

.song-title-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: 3px;
}

.song-title {
  font-size: var(--text-base);
  font-weight: 500;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.song-title.clickable:hover {
  color: var(--accent);
  cursor: pointer;
}

.song-mode-badge {
  font-size: 10px;
  font-family: "JetBrains Mono", monospace;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-dim);
  border: 1px solid var(--border-strong);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.song-meta {
  font-size: var(--text-xs);
  color: var(--text-dim);
  display: flex;
  gap: 4px;
  align-items: center;
  flex-wrap: wrap;
}

.status-label {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  font-size: 10px;
}
.status-label.completed {
  color: var(--success);
}
.status-label.running,
.status-label.pending {
  color: var(--accent);
}
.status-label.failed {
  color: var(--danger);
}

.progress-track {
  margin-top: var(--space-2);
  height: 3px;
  background: var(--bg-sunken);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.3s ease;
  border-radius: inherit;
}

/* Features grid */
.features {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-4);
}

@media (min-width: 900px) {
  .features {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
