// Singleton Tone.Sampler serving the Salamander Grand Piano samples hosted
// on tonejs.github.io. First access downloads ~3 MB of mp3 samples; every
// component that plays MIDI shares the same instance.
import * as Tone from "tone";

const SALAMANDER_URLS: Record<string, string> = {
  A0: "A0.mp3",
  C1: "C1.mp3",
  "D#1": "Ds1.mp3",
  "F#1": "Fs1.mp3",
  A1: "A1.mp3",
  C2: "C2.mp3",
  "D#2": "Ds2.mp3",
  "F#2": "Fs2.mp3",
  A2: "A2.mp3",
  C3: "C3.mp3",
  "D#3": "Ds3.mp3",
  "F#3": "Fs3.mp3",
  A3: "A3.mp3",
  C4: "C4.mp3",
  "D#4": "Ds4.mp3",
  "F#4": "Fs4.mp3",
  A4: "A4.mp3",
  C5: "C5.mp3",
  "D#5": "Ds5.mp3",
  "F#5": "Fs5.mp3",
  A5: "A5.mp3",
  C6: "C6.mp3",
  "D#6": "Ds6.mp3",
  "F#6": "Fs6.mp3",
  A6: "A6.mp3",
  C7: "C7.mp3",
  "D#7": "Ds7.mp3",
  "F#7": "Fs7.mp3",
  A7: "A7.mp3",
  C8: "C8.mp3",
};

let samplerInstance: Tone.Sampler | null = null;
let loadPromise: Promise<Tone.Sampler> | null = null;

const isLoaded = ref(false);
const isLoading = ref(false);

export function usePianoSampler() {
  async function getSampler(): Promise<Tone.Sampler> {
    if (samplerInstance && isLoaded.value) {
      return samplerInstance;
    }
    if (loadPromise) {
      return loadPromise;
    }

    isLoading.value = true;
    loadPromise = (async () => {
      await Tone.start();

      samplerInstance = new Tone.Sampler({
        urls: SALAMANDER_URLS,
        release: 1,
        baseUrl: "https://tonejs.github.io/audio/salamander/",
      }).toDestination();

      samplerInstance.volume.value = -6;

      await Tone.loaded();

      isLoaded.value = true;
      isLoading.value = false;
      return samplerInstance;
    })();

    try {
      return await loadPromise;
    } catch (err) {
      loadPromise = null;
      isLoading.value = false;
      throw err;
    }
  }

  return {
    getSampler,
    isLoaded: readonly(isLoaded),
    isLoading: readonly(isLoading),
  };
}
