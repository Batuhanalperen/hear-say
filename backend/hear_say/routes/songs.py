"""Song endpoints: upload, list, detail, status polling, file downloads."""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from hear_say.config import DATA_DIR, OUTPUTS_DIR, UPLOADS_DIR
from hear_say.db import get_session
from hear_say.jobs import process_song
from hear_say.models import Song, SongMode, SongStatus

router = APIRouter(prefix="/api/songs", tags=["songs"])


ALLOWED_AUDIO_EXTS = {".mp3", ".wav", ".flac", ".ogg", ".m4a"}

# Demucs htdemucs_6s stems
DEMUCS_STEM_NAMES = ("vocals", "drums", "bass", "other", "piano", "guitar")

# Full list of stems exposed via the debug player (Demucs + BS-Roformer outputs)
ALL_STEM_NAMES = DEMUCS_STEM_NAMES + (
    "bs_roformer_vocals",
    "bs_roformer_instrumental",
)


def _find_available_stems(song_id: int) -> list[str]:
    """List every stem wav produced for this song.

    Looks at both Demucs output (`outputs/<id>/stems/...`) and BS-Roformer
    output (`outputs/<id>/vocal_removed/...`).
    """
    song_root = OUTPUTS_DIR / str(song_id)
    if not song_root.exists():
        return []

    available: list[str] = []

    demucs_dir = song_root / "stems"
    if demucs_dir.exists():
        for name in DEMUCS_STEM_NAMES:
            for _ in demucs_dir.rglob(f"{name}.wav"):
                available.append(name)
                break

    vocal_removed_dir = song_root / "vocal_removed"
    if vocal_removed_dir.exists():
        for wav in vocal_removed_dir.glob("*.wav"):
            lower = wav.stem.lower()
            if ("vocals" in lower or "vocal" in lower) and "bs_roformer_vocals" not in available:
                available.append("bs_roformer_vocals")
            elif ("instrumental" in lower or "music" in lower) and "bs_roformer_instrumental" not in available:
                available.append("bs_roformer_instrumental")

    return available


def _find_stem_path(song_id: int, stem_name: str) -> Path | None:
    """Resolve a stem name to an actual wav path on disk."""
    if stem_name not in ALL_STEM_NAMES:
        return None

    song_root = OUTPUTS_DIR / str(song_id)
    if not song_root.exists():
        return None

    if stem_name in DEMUCS_STEM_NAMES:
        demucs_dir = song_root / "stems"
        if demucs_dir.exists():
            for wav in demucs_dir.rglob(f"{stem_name}.wav"):
                return wav
        return None

    if stem_name.startswith("bs_roformer_"):
        kind = stem_name.replace("bs_roformer_", "")
        vocal_removed_dir = song_root / "vocal_removed"
        if vocal_removed_dir.exists():
            for wav in vocal_removed_dir.glob("*.wav"):
                lower = wav.stem.lower()
                if kind == "vocals" and ("vocals" in lower or "vocal" in lower):
                    return wav
                if kind == "instrumental" and ("instrumental" in lower or "music" in lower):
                    return wav
    return None


@router.post("/upload")
async def upload_song(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    mode: SongMode = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> dict:
    """Accept an audio file and enqueue it for transcription."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {ext}. Allowed: {sorted(ALLOWED_AUDIO_EXTS)}",
        )

    unique_id = uuid.uuid4().hex[:12]
    stored_name = f"{unique_id}_{Path(file.filename).name}"
    dest_path = UPLOADS_DIR / stored_name

    with dest_path.open("wb") as buf:
        shutil.copyfileobj(file.file, buf)

    song = Song(
        title=title,
        original_filename=file.filename,
        mode=mode,
        status=SongStatus.pending,
        current_step="queued",
        progress_pct=0,
        audio_path=str(dest_path.relative_to(DATA_DIR)),
    )
    session.add(song)
    session.commit()
    session.refresh(song)

    background_tasks.add_task(process_song, song.id)

    return {
        "id": song.id,
        "title": song.title,
        "status": song.status,
        "mode": song.mode,
    }


@router.get("")
def list_songs(session: Session = Depends(get_session)) -> list[dict]:
    """List all songs, newest first."""
    songs = session.exec(select(Song).order_by(Song.created_at.desc())).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "original_filename": s.original_filename,
            "mode": s.mode,
            "status": s.status,
            "current_step": s.current_step,
            "progress_pct": s.progress_pct,
            "duration_seconds": s.duration_seconds,
            "created_at": s.created_at.isoformat(),
            "has_levels": bool(s.levels),
        }
        for s in songs
    ]


@router.get("/{song_id}")
def get_song(song_id: int, session: Session = Depends(get_session)) -> dict:
    """Return full song detail including level files and available stems."""
    song = session.get(Song, song_id)
    if song is None:
        raise HTTPException(status_code=404, detail="Song not found")

    return {
        "id": song.id,
        "title": song.title,
        "original_filename": song.original_filename,
        "mode": song.mode,
        "status": song.status,
        "current_step": song.current_step,
        "progress_pct": song.progress_pct,
        "error_message": song.error_message,
        "duration_seconds": song.duration_seconds,
        "levels": song.levels,
        "stems": _find_available_stems(song.id),
        "created_at": song.created_at.isoformat(),
        "updated_at": song.updated_at.isoformat(),
    }


@router.get("/{song_id}/status")
def get_song_status(song_id: int, session: Session = Depends(get_session)) -> dict:
    """Lightweight polling endpoint for progress updates."""
    song = session.get(Song, song_id)
    if song is None:
        raise HTTPException(status_code=404, detail="Song not found")
    return {
        "id": song.id,
        "status": song.status,
        "current_step": song.current_step,
        "progress_pct": song.progress_pct,
        "error_message": song.error_message,
    }


@router.get("/{song_id}/files/{level_name}/{kind}")
def download_level_file(
    song_id: int,
    level_name: str,
    kind: str,
    session: Session = Depends(get_session),
) -> FileResponse:
    """Download a level file (kind = 'midi' or 'musicxml')."""
    if kind not in ("midi", "musicxml"):
        raise HTTPException(status_code=400, detail="kind must be 'midi' or 'musicxml'")

    song = session.get(Song, song_id)
    if song is None:
        raise HTTPException(status_code=404, detail="Song not found")

    level = song.levels.get(level_name) if song.levels else None
    if not level:
        raise HTTPException(status_code=404, detail=f"Level not found: {level_name}")

    rel_path = level.get(kind)
    if not rel_path:
        raise HTTPException(status_code=404, detail=f"File kind missing: {kind}")

    abs_path = DATA_DIR / rel_path
    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="File missing on disk")

    media_type = "audio/midi" if kind == "midi" else "application/vnd.recordare.musicxml+xml"
    filename = f"{song.title}_{level_name}.{'mid' if kind == 'midi' else 'musicxml'}"
    return FileResponse(abs_path, media_type=media_type, filename=filename)


@router.get("/{song_id}/stems/{stem_name}")
def download_stem(
    song_id: int,
    stem_name: str,
    session: Session = Depends(get_session),
) -> FileResponse:
    """Download a separation stem wav (for debugging)."""
    song = session.get(Song, song_id)
    if song is None:
        raise HTTPException(status_code=404, detail="Song not found")

    stem_path = _find_stem_path(song_id, stem_name)
    if stem_path is None or not stem_path.exists():
        raise HTTPException(status_code=404, detail=f"Stem not found: {stem_name}")

    return FileResponse(
        stem_path,
        media_type="audio/wav",
        filename=f"{song.title}_{stem_name}.wav",
    )


@router.get("/{song_id}/audio")
def download_original_audio(
    song_id: int,
    session: Session = Depends(get_session),
) -> FileResponse:
    """Return the original uploaded audio file."""
    song = session.get(Song, song_id)
    if song is None:
        raise HTTPException(status_code=404, detail="Song not found")

    abs_path = DATA_DIR / song.audio_path
    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="Audio file missing")

    return FileResponse(abs_path, filename=song.original_filename)


@router.delete("/{song_id}")
def delete_song(song_id: int, session: Session = Depends(get_session)) -> dict:
    """Delete a song's database row and all its on-disk artifacts."""
    song = session.get(Song, song_id)
    if song is None:
        raise HTTPException(status_code=404, detail="Song not found")

    audio_abs = DATA_DIR / song.audio_path
    if audio_abs.exists():
        audio_abs.unlink(missing_ok=True)

    song_output = OUTPUTS_DIR / str(song.id)
    if song_output.exists():
        shutil.rmtree(song_output, ignore_errors=True)

    session.delete(song)
    session.commit()

    return {"ok": True, "id": song_id}
