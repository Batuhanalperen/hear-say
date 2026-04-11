<script setup lang="ts">
const props = defineProps<{
  songId: number;
  midiUrl: string;
}>();

const { isPlaying, loading, toggle } = useQuickPlay();
const playing = computed(() => isPlaying(props.songId));

function handleClick(e: Event) {
  e.preventDefault();
  e.stopPropagation();
  toggle(props.songId, props.midiUrl);
}
</script>

<template>
  <button
    class="qp-btn"
    :class="{ 'is-playing': playing }"
    :title="playing ? 'Stop preview' : 'Preview melody'"
    :aria-label="playing ? 'Stop preview' : 'Play preview'"
    @click="handleClick"
  >
    <div v-if="loading" class="i-tabler-loader-2 animate-spin" />
    <div v-else-if="playing" class="i-tabler-player-stop-filled" />
    <div v-else class="i-tabler-player-play-filled" />
  </button>
</template>

<style scoped>
.qp-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background: var(--bg-raised);
  border: 1px solid var(--border-strong);
  color: var(--text-muted);
  font-size: 16px;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.qp-btn:hover {
  background: var(--accent-bg);
  border-color: var(--accent);
  color: var(--accent);
  transform: scale(1.04);
}

.qp-btn.is-playing {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--accent-contrast);
}

.qp-btn.is-playing:hover {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
}

.qp-btn:active {
  transform: scale(0.96);
}
</style>
