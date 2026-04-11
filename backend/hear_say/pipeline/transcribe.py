"""Piano transcription via ByteDance Piano Transcription.

The model is piano-specific, trained on MAESTRO, and produces very clean MIDI
on both solo piano recordings and pre-separated piano stems.

We don't use `piano_transcription_inference.load_audio` because its internal
`librosa.core.audio` namespace was removed in librosa 0.10+. Instead we load
audio ourselves with `librosa.load` and pass a numpy array directly to
`transcriptor.transcribe()`.
"""
from __future__ import annotations

from pathlib import Path


def transcribe_piano(
    audio_path: Path,
    output_dir: Path,
    *,
    device: str = "cuda",
) -> Path:
    """Transcribe a piano audio file to MIDI.

    Args:
        audio_path: Input audio file (mp3, wav, flac, ogg).
        output_dir: Directory where the MIDI file will be written.
        device: "cuda" or "cpu".

    Returns:
        Path to the generated MIDI file.
    """
    import librosa
    from piano_transcription_inference import (
        PianoTranscription,
        sample_rate as PT_SAMPLE_RATE,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    midi_path = output_dir / f"{audio_path.stem}_piano_transcription.mid"

    # Model expects mono float32 at its configured sample rate (16 kHz)
    audio, _ = librosa.load(str(audio_path), sr=PT_SAMPLE_RATE, mono=True)

    transcriptor = PianoTranscription(device=device, checkpoint_path=None)
    transcriptor.transcribe(audio, str(midi_path))

    if not midi_path.exists():
        raise FileNotFoundError(
            f"Piano transcription did not produce expected output: {midi_path}"
        )
    return midi_path
