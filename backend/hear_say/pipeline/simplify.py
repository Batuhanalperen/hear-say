"""Post-processing: minimal denoise pass and MusicXML export.

ByteDance Piano Transcription produces high-quality MIDI — aggressive filters
remove real notes and should be avoided. `_denoise_notes` has intentionally
loose defaults and mostly acts as a safety net for obvious artifacts.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pretty_midi


PIANO_PROGRAM = 0  # General MIDI Acoustic Grand Piano


@dataclass
class LevelOutput:
    """Filesystem output for one processed level."""

    name: str
    midi_path: Path
    musicxml_path: Path | None = None


def _collect_notes(midi: pretty_midi.PrettyMIDI) -> list[pretty_midi.Note]:
    """Gather all non-drum notes from a MIDI file."""
    notes: list[pretty_midi.Note] = []
    for inst in midi.instruments:
        if inst.is_drum:
            continue
        notes.extend(inst.notes)
    return notes


def _denoise_notes(
    notes: list[pretty_midi.Note],
    *,
    min_velocity: int = 1,
    min_duration: float = 0.01,
    ghost_ratio: float = 0.0,
    min_pitch: int = 21,   # A0
    max_pitch: int = 108,  # C8
) -> list[pretty_midi.Note]:
    """Drop obvious artifacts; leave real notes alone.

    Filters applied in order:
      1. Pitch range — anything outside A0..C8 is not a piano note.
      2. Minimum velocity — velocity 0 is a phantom event.
      3. Minimum duration — sub-10 ms "notes" are transients.
      4. Ghost filter (disabled by default) — a note whose concurrent neighbours
         are all `ghost_ratio`x louder is treated as a harmonic overtone.
    """
    filtered = [
        n for n in notes
        if min_pitch <= n.pitch <= max_pitch
        and n.velocity >= min_velocity
        and (n.end - n.start) >= min_duration
    ]

    if not filtered or ghost_ratio <= 0:
        return filtered

    filtered_sorted = sorted(filtered, key=lambda n: n.start)
    result: list[pretty_midi.Note] = []

    for i, note in enumerate(filtered_sorted):
        max_concurrent_velocity = 0

        j = i - 1
        while j >= 0 and filtered_sorted[j].end > note.start:
            other = filtered_sorted[j]
            if other.end > note.start and other.start < note.end:
                max_concurrent_velocity = max(max_concurrent_velocity, other.velocity)
            j -= 1
            if i - j > 30:
                break

        for k in range(i + 1, len(filtered_sorted)):
            other = filtered_sorted[k]
            if other.start >= note.end:
                break
            if other.start < note.end and other.end > note.start:
                max_concurrent_velocity = max(max_concurrent_velocity, other.velocity)

        if (
            max_concurrent_velocity > 0
            and note.velocity < max_concurrent_velocity * ghost_ratio
        ):
            continue

        result.append(note)

    return result


def _build_piano_midi(
    notes: list[pretty_midi.Note],
    tempo_bpm: float = 120.0,
) -> pretty_midi.PrettyMIDI:
    """Wrap a note list in a single Acoustic Grand Piano instrument."""
    out = pretty_midi.PrettyMIDI(initial_tempo=tempo_bpm)
    instrument = pretty_midi.Instrument(program=PIANO_PROGRAM, name="Piano")
    instrument.notes = sorted(notes, key=lambda n: (n.start, n.pitch))
    out.instruments.append(instrument)
    return out


def export_musicxml(midi_path: Path, musicxml_path: Path) -> Path:
    """Convert a MIDI file to MusicXML for sheet music rendering."""
    import music21

    score = music21.converter.parse(str(midi_path))
    musicxml_path.parent.mkdir(parents=True, exist_ok=True)
    score.write("musicxml", fp=str(musicxml_path))
    return musicxml_path


def simplify_midi(
    source_midi_path: Path,
    output_dir: Path,
    *,
    levels: list[str] | None = None,  # kept for backward-compatibility
    export_xml: bool = True,
) -> list[LevelOutput]:
    """Denoise the raw MIDI and emit MIDI + MusicXML files.

    The schema supports multiple levels but today only "raw" is produced.
    """
    source_midi = pretty_midi.PrettyMIDI(str(source_midi_path))
    output_dir.mkdir(parents=True, exist_ok=True)

    notes = _denoise_notes(_collect_notes(source_midi))
    tempo = source_midi.estimate_tempo() or 120.0
    cleaned = _build_piano_midi(notes, tempo_bpm=tempo)

    midi_out = output_dir / "raw.mid"
    cleaned.write(str(midi_out))

    musicxml_out: Path | None = None
    if export_xml:
        try:
            musicxml_out = output_dir / "raw.musicxml"
            export_musicxml(midi_out, musicxml_out)
        except Exception as exc:
            print(f"[warning] MusicXML export failed: {exc}")
            musicxml_out = None

    return [
        LevelOutput(
            name="raw",
            midi_path=midi_out,
            musicxml_path=musicxml_out,
        )
    ]


# Legacy alias for callers that inspect available levels
LEVEL_BUILDERS: dict[str, object] = {"raw": _build_piano_midi}
