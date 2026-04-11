// Global quick-play state — only one song can be previewed at a time.
// Each row on the history page shares this state so clicking "play" on one
// song automatically stops whatever was playing before.
import { Midi } from "@tonejs/midi";
import * as Tone from "tone";

const currentSongId = ref<number | null>(null);
const loading = ref(false);

function stopInternal() {
  Tone.getTransport().stop();
  Tone.getTransport().cancel();
  currentSongId.value = null;
}

export function useQuickPlay() {
  const isPlaying = (songId: number) => currentSongId.value === songId;

  async function toggle(songId: number, midiUrl: string) {
    if (currentSongId.value === songId) {
      stopInternal();
      return;
    }
    if (currentSongId.value !== null) {
      stopInternal();
    }

    loading.value = true;
    try {
      const res = await fetch(midiUrl);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const buffer = await res.arrayBuffer();
      if (buffer.byteLength === 0) throw new Error("Empty MIDI file");

      const midi = new Midi(buffer);
      if (!midi.header) throw new Error("MIDI parse failed (no header)");

      await Tone.start();
      const { getSampler } = usePianoSampler();
      const sampler = await getSampler();

      Tone.getTransport().stop();
      Tone.getTransport().cancel();
      Tone.getTransport().position = 0;

      for (const track of midi.tracks) {
        for (const note of track.notes) {
          Tone.getTransport().schedule((time) => {
            sampler.triggerAttackRelease(
              note.name,
              note.duration,
              time,
              note.velocity,
            );
          }, note.time);
        }
      }

      Tone.getTransport().schedule(() => {
        stopInternal();
      }, midi.duration + 0.5);

      Tone.getTransport().start();
      currentSongId.value = songId;
    } catch (err) {
      console.error("useQuickPlay error:", err);
      currentSongId.value = null;
    } finally {
      loading.value = false;
    }
  }

  return {
    isPlaying,
    loading: readonly(loading),
    toggle,
    stop: stopInternal,
  };
}
