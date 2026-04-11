"""Developer CLI for running the pipeline without the web UI.

Useful for quick quality checks:

    python -m hear_say.cli check
    python -m hear_say.cli transcribe path/to/song.mp3 --mode solo
    python -m hear_say.cli simplify path/to/song.mid
"""
from __future__ import annotations

import sys
import time
from enum import Enum
from pathlib import Path

# Force UTF-8 on Windows consoles that default to cp1252
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="hear-say",
    help="Audio to piano MIDI transcription.",
    no_args_is_help=True,
)
console = Console(legacy_windows=False, force_terminal=True)


class TranscriptionMode(str, Enum):
    solo = "solo"
    full_band = "full-band"


@app.command()
def transcribe(
    audio_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Input audio file (mp3, wav, flac, ogg)",
    ),
    mode: TranscriptionMode = typer.Option(
        TranscriptionMode.solo,
        "--mode",
        "-m",
        help="solo: direct piano transcription | full-band: separate stems first",
    ),
    output_dir: Path = typer.Option(
        Path("outputs"),
        "--output-dir",
        "-o",
        help="Output directory",
    ),
    keep_stems: bool = typer.Option(
        False,
        "--keep-stems",
        help="Keep Demucs intermediate stems (full-band mode only)",
    ),
    device: str = typer.Option(
        "cuda",
        "--device",
        help="cuda | cpu",
    ),
) -> None:
    """Transcribe an audio file to piano MIDI."""
    from hear_say.pipeline.separate import cleanup_stems, separate_stems
    from hear_say.pipeline.transcribe import transcribe_piano

    track_name = audio_file.stem
    work_dir = output_dir / track_name
    work_dir.mkdir(parents=True, exist_ok=True)

    timings: dict[str, float] = {}
    results: dict[str, Path] = {}

    console.print("[bold cyan]hear-say[/] transcription")
    console.print(f"  Input:  [yellow]{audio_file}[/]")
    console.print(f"  Mode:   [green]{mode.value}[/]")
    console.print(f"  Device: [green]{device}[/]")
    console.print(f"  Output: [yellow]{work_dir}[/]\n")

    if mode == TranscriptionMode.solo:
        piano_source = audio_file
    else:
        console.print("[cyan]>[/] Demucs 6-stem separation (htdemucs_6s)")
        t0 = time.perf_counter()
        stems = separate_stems(
            audio_file,
            work_dir / "stems",
            device=device,
        )
        timings["demucs"] = time.perf_counter() - t0
        console.print(
            f"  [green]OK[/] {len(stems)} stems ({timings['demucs']:.1f}s)"
        )
        for name, path in stems.items():
            console.print(f"    - {name}: {path.name}")

        if "piano" not in stems:
            console.print("[red]FAILED[/] Demucs produced no piano stem")
            raise typer.Exit(code=1)
        piano_source = stems["piano"]

        if not keep_stems:
            cleanup_stems(stems)
            console.print("  [dim](intermediate stem wavs removed)[/]")

    console.print("\n[cyan]>[/] Piano transcription (ByteDance)")
    t0 = time.perf_counter()
    midi_path = transcribe_piano(
        piano_source,
        work_dir / "raw",
        device=device,
    )
    timings["piano_transcription"] = time.perf_counter() - t0
    results["piano"] = midi_path
    console.print(
        f"  [green]OK[/] {midi_path.name} ({timings['piano_transcription']:.1f}s)"
    )

    console.print()
    table = Table(title="Timings")
    table.add_column("Step", style="cyan")
    table.add_column("Duration", justify="right", style="green")
    total = 0.0
    for name, dur in timings.items():
        table.add_row(name, f"{dur:.2f}s")
        total += dur
    table.add_row("[bold]Total[/]", f"[bold]{total:.2f}s[/]")
    console.print(table)

    console.print("\n[bold green]Generated MIDI files:[/]")
    for label, path in results.items():
        console.print(f"  [yellow]{label:10}[/] -> {path}")


@app.command()
def simplify(
    midi_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Raw MIDI file (piano transcription output)",
    ),
    output_dir: Path = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory (default: <midi_file>'s sibling 'levels/')",
    ),
    no_xml: bool = typer.Option(
        False,
        "--no-xml",
        help="Skip MusicXML export",
    ),
) -> None:
    """Denoise a raw MIDI and emit cleaned MIDI + MusicXML."""
    from hear_say.pipeline.simplify import simplify_midi

    if output_dir is None:
        output_dir = midi_file.parent.parent / "levels"

    console.print("[bold cyan]hear-say[/] post-processing")
    console.print(f"  Input:  [yellow]{midi_file}[/]")
    console.print(f"  Output: [yellow]{output_dir}[/]\n")

    t0 = time.perf_counter()
    outputs = simplify_midi(
        midi_file,
        output_dir,
        export_xml=not no_xml,
    )
    elapsed = time.perf_counter() - t0

    console.print(f"[green]OK[/] {len(outputs)} file(s) produced ({elapsed:.1f}s)\n")

    table = Table(title="Outputs")
    table.add_column("Level", style="cyan")
    table.add_column("MIDI", style="yellow")
    table.add_column("MusicXML", style="yellow")

    for out in outputs:
        xml_cell = str(out.musicxml_path.name) if out.musicxml_path else "[dim]-[/]"
        table.add_row(out.name, out.midi_path.name, xml_cell)

    console.print(table)


@app.command()
def check() -> None:
    """Verify GPU and dependencies are available."""
    console.print("[bold cyan]hear-say[/] environment check\n")

    try:
        import torch
        console.print(f"  [green]OK[/] torch {torch.__version__}")
        if torch.cuda.is_available():
            gpu = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
            console.print(f"  [green]OK[/] CUDA — {gpu} ({vram:.1f} GB VRAM)")
        else:
            console.print("  [yellow]![/] CUDA unavailable — falling back to CPU")
    except ImportError:
        console.print("  [red]X[/] torch not installed")

    for module_name, label in [
        ("piano_transcription_inference", "piano_transcription_inference"),
        ("audio_separator", "audio-separator"),
        ("demucs", "demucs"),
        ("music21", "music21"),
    ]:
        try:
            __import__(module_name)
            console.print(f"  [green]OK[/] {label}")
        except ImportError:
            console.print(f"  [red]X[/] {label} not installed")


if __name__ == "__main__":
    app()
