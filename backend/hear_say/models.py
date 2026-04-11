"""Database models."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class SongMode(str, Enum):
    solo = "solo"
    full_band = "full-band"


class SongStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Song(SQLModel, table=True):
    """One uploaded audio file and its transcription status.

    `levels` is a JSON column for historical reasons (the pipeline used to
    produce multiple difficulty levels). Today only the "raw" level is
    populated, but the schema is kept backward-compatible.
    """

    id: int | None = Field(default=None, primary_key=True)
    title: str
    original_filename: str
    mode: SongMode
    status: SongStatus = Field(default=SongStatus.pending)
    current_step: str | None = None
    progress_pct: int = 0
    error_message: str | None = None

    # File paths, stored relative to DATA_DIR
    audio_path: str
    raw_midi_path: str | None = None

    levels: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    duration_seconds: float | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
