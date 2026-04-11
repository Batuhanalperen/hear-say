"""Audio source separation.

Two separators are used in sequence (full-band mode):

1. `isolate_instrumental` runs BS-Roformer via `audio-separator` to strip the
   vocals from the mix — this is the current SOTA for vocal separation.
2. `separate_stems` runs Demucs `htdemucs_6s` on the vocal-free instrumental
   to split it into six stems (vocals, drums, bass, other, piano, guitar).
   Feeding vocal-free audio to Demucs gives a significantly cleaner piano stem
   than running Demucs alone on the full mix.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


DEMUCS_MODEL = "htdemucs_6s"

# Demucs quality settings. Higher values = slower but more accurate separation.
DEFAULT_SHIFTS = 5
DEFAULT_OVERLAP = 0.5

STEM_NAMES = ("vocals", "drums", "bass", "other", "piano", "guitar")

BS_ROFORMER_MODEL = "model_bs_roformer_ep_317_sdr_12.9755.ckpt"


def separate_stems(
    audio_path: Path,
    output_dir: Path,
    *,
    model: str = DEMUCS_MODEL,
    device: str = "cuda",
    shifts: int = DEFAULT_SHIFTS,
    overlap: float = DEFAULT_OVERLAP,
) -> dict[str, Path]:
    """Run Demucs and return a dict mapping stem name to wav path."""
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "demucs.separate",
        "-n", model,
        "-d", device,
        "--shifts", str(shifts),
        "--overlap", str(overlap),
        "-o", str(output_dir),
        str(audio_path),
    ]

    # encoding="utf-8" + errors="replace": Demucs emits non-UTF-8 bytes on
    # Windows hosts when capturing output; decode tolerantly.
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Demucs failed (exit {result.returncode}):\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    # Layout: <output_dir>/<model>/<track_stem>/<stem>.wav
    track_stem = audio_path.stem
    stem_dir = output_dir / model / track_stem

    stems: dict[str, Path] = {}
    for stem_name in STEM_NAMES:
        stem_file = stem_dir / f"{stem_name}.wav"
        if stem_file.exists():
            stems[stem_name] = stem_file

    if not stems:
        raise FileNotFoundError(
            f"Demucs produced no stems. Expected directory: {stem_dir}"
        )

    return stems


def cleanup_stems(stem_paths: dict[str, Path]) -> None:
    """Remove the stem output directory (optional — stems are kept for debug)."""
    if not stem_paths:
        return
    stem_dir = next(iter(stem_paths.values())).parent
    if stem_dir.exists():
        shutil.rmtree(stem_dir)


def isolate_instrumental(
    audio_path: Path,
    output_dir: Path,
    *,
    model_filename: str = BS_ROFORMER_MODEL,
) -> Path:
    """Strip vocals from a full mix using BS-Roformer.

    Returns the path to the generated instrumental wav, which can then be fed
    to `separate_stems` for a cleaner piano stem.
    """
    from audio_separator.separator import Separator

    output_dir.mkdir(parents=True, exist_ok=True)

    separator = Separator(
        output_dir=str(output_dir),
        output_format="WAV",
    )
    separator.load_model(model_filename=model_filename)

    output_names = separator.separate(str(audio_path))

    instrumental_path: Path | None = None
    for name in output_names:
        candidate = output_dir / name
        if not candidate.exists():
            candidate = Path(name)
        lower = name.lower()
        if "instrumental" in lower or "music" in lower:
            instrumental_path = candidate
            break

    if instrumental_path is None or not instrumental_path.exists():
        raise RuntimeError(
            f"audio-separator did not produce an instrumental stem. "
            f"Outputs: {output_names}"
        )

    return instrumental_path
