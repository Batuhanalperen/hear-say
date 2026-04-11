"""Background transcription pipeline worker.

Called by FastAPI `BackgroundTasks` after a successful upload. Updates the
`Song` row with progress as it runs and sets `status` to `completed` or
`failed` at the end.

Pipeline:
    Solo mode:       audio -> ByteDance -> denoise/MusicXML
    Full-band mode:  audio -> BS-Roformer -> instrumental
                           -> Demucs htdemucs_6s -> piano stem
                           -> ByteDance -> denoise/MusicXML
"""
from __future__ import annotations

import traceback
from datetime import datetime
from pathlib import Path

import pretty_midi
from sqlmodel import Session

from hear_say.config import DATA_DIR, DEFAULT_DEVICE, OUTPUTS_DIR
from hear_say.db import engine
from hear_say.models import Song, SongMode, SongStatus
from hear_say.pipeline.separate import isolate_instrumental, separate_stems
from hear_say.pipeline.simplify import simplify_midi
from hear_say.pipeline.transcribe import transcribe_piano


def _rel(path: Path) -> str:
    """Return a path relative to DATA_DIR (for storage in the DB)."""
    try:
        return str(path.resolve().relative_to(DATA_DIR))
    except ValueError:
        return str(path)


def _update_song(
    session: Session,
    song: Song,
    *,
    status: SongStatus | None = None,
    current_step: str | None = None,
    progress_pct: int | None = None,
    error_message: str | None = None,
    raw_midi_path: str | None = None,
    levels: dict | None = None,
    duration_seconds: float | None = None,
) -> None:
    """Partial update helper — only touches fields that were passed."""
    if status is not None:
        song.status = status
    if current_step is not None:
        song.current_step = current_step
    if progress_pct is not None:
        song.progress_pct = progress_pct
    if error_message is not None:
        song.error_message = error_message
    if raw_midi_path is not None:
        song.raw_midi_path = raw_midi_path
    if levels is not None:
        song.levels = levels
    if duration_seconds is not None:
        song.duration_seconds = duration_seconds
    song.updated_at = datetime.utcnow()
    session.add(song)
    session.commit()
    session.refresh(song)


def process_song(song_id: int) -> None:
    """Run the pipeline for a single song."""
    with Session(engine) as session:
        song = session.get(Song, song_id)
        if song is None:
            return

        try:
            _update_song(
                session,
                song,
                status=SongStatus.running,
                current_step="preparing",
                progress_pct=5,
            )

            audio_path = (DATA_DIR / song.audio_path).resolve()
            song_output = OUTPUTS_DIR / str(song.id)
            song_output.mkdir(parents=True, exist_ok=True)

            raw_dir = song_output / "raw"
            raw_dir.mkdir(exist_ok=True)

            # --- 1. Get piano-only audio ---
            if song.mode == SongMode.solo:
                piano_audio_source = audio_path
            else:
                # Step 1a: vocal removal via BS-Roformer
                _update_song(
                    session,
                    song,
                    current_step="isolating vocals (BS-Roformer)",
                    progress_pct=15,
                )
                vocal_removed_dir = song_output / "vocal_removed"
                instrumental_path = isolate_instrumental(
                    audio_path, vocal_removed_dir
                )

                # Step 1b: multi-stem separation on the vocal-free instrumental
                _update_song(
                    session,
                    song,
                    current_step="isolating piano stem (Demucs htdemucs_6s)",
                    progress_pct=35,
                )
                stems_dir = song_output / "stems"
                stems = separate_stems(
                    instrumental_path, stems_dir, device=DEFAULT_DEVICE
                )

                if "piano" not in stems:
                    raise RuntimeError(
                        "Demucs htdemucs_6s did not produce a piano stem. "
                        f"Available stems: {list(stems.keys())}"
                    )

                piano_audio_source = stems["piano"]

            # --- 2. Piano transcription ---
            _update_song(
                session,
                song,
                current_step="piano transcription (ByteDance)",
                progress_pct=55,
            )
            primary_midi = transcribe_piano(
                piano_audio_source,
                raw_dir,
                device=DEFAULT_DEVICE,
            )

            try:
                midi_obj = pretty_midi.PrettyMIDI(str(primary_midi))
                duration = midi_obj.get_end_time()
            except Exception:
                duration = None

            # --- 3. Denoise + MusicXML export ---
            _update_song(
                session,
                song,
                current_step="post-processing (denoise + MusicXML)",
                progress_pct=80,
                raw_midi_path=_rel(primary_midi),
                duration_seconds=duration,
            )

            levels_dir = song_output / "levels"
            level_outputs = simplify_midi(primary_midi, levels_dir, export_xml=True)

            levels_dict: dict[str, dict] = {}
            for level in level_outputs:
                levels_dict[level.name] = {
                    "midi": _rel(level.midi_path),
                    "musicxml": _rel(level.musicxml_path)
                    if level.musicxml_path
                    else None,
                }

            _update_song(
                session,
                song,
                status=SongStatus.completed,
                current_step="completed",
                progress_pct=100,
                levels=levels_dict,
            )

        except Exception as exc:
            tb = traceback.format_exc()
            _update_song(
                session,
                song,
                status=SongStatus.failed,
                current_step="failed",
                error_message=f"{exc}\n\n{tb}",
            )
            print(f"[jobs] Song {song_id} failed: {exc}\n{tb}")
