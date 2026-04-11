"""Runtime configuration. All values come from environment variables with
sensible defaults so the app works out of the box when started via Docker.
"""
from __future__ import annotations

import os
from pathlib import Path


# Base data directory (bind-mounted from the host in docker-compose)
DATA_DIR = Path(os.getenv("HEAR_SAY_DATA_DIR", "./data")).resolve()

UPLOADS_DIR = DATA_DIR / "uploads"
OUTPUTS_DIR = DATA_DIR / "outputs"
DB_PATH = DATA_DIR / "hear-say.db"
DB_URL = f"sqlite:///{DB_PATH}"

# "cuda" (default) or "cpu". CPU mode works but is impractically slow.
DEFAULT_DEVICE = os.getenv("HEAR_SAY_DEVICE", "cuda")

# Nuxt SPA build output, copied into the image at build time
FRONTEND_DIST_DIR = Path(
    os.getenv("HEAR_SAY_FRONTEND_DIST", "./frontend_dist")
).resolve()


def ensure_dirs() -> None:
    """Create required subdirectories on startup if they don't exist."""
    for d in (DATA_DIR, UPLOADS_DIR, OUTPUTS_DIR):
        d.mkdir(parents=True, exist_ok=True)
