"""FastAPI entry point.

Routes:
    /api/health             — health check
    /api/songs/...          — upload, list, detail, status, file download
    /                       — Nuxt SPA static files (with client-side routing fallback)
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.types import Scope

from hear_say import __version__
from hear_say.config import FRONTEND_DIST_DIR, ensure_dirs
from hear_say.db import init_db
from hear_say.routes import songs


class SPAStaticFiles(StaticFiles):
    """StaticFiles that falls back to index.html for unknown routes.

    Nuxt runs as an SPA in the browser — vue-router handles routes like
    /songs/1 on the client, but a cold page load hits the server first. This
    subclass serves index.html for any path the filesystem doesn't match,
    letting the client-side router take over.
    """

    async def get_response(self, path: str, scope: Scope):
        response = await super().get_response(path, scope)
        if response.status_code == 404:
            response = await super().get_response("index.html", scope)
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    ensure_dirs()
    init_db()
    yield


app = FastAPI(
    title="hear-say",
    version=__version__,
    description="Audio to piano MIDI transcription",
    lifespan=lifespan,
)

# Everything is served from the same origin in production, but enable CORS for
# development setups that hit the backend directly from a separate dev server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:7777",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:7777",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    import torch

    return {
        "status": "ok",
        "version": __version__,
        "cuda": torch.cuda.is_available(),
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
    }


app.include_router(songs.router)


# Mount the SPA last so API routes take precedence
if FRONTEND_DIST_DIR.exists() and (FRONTEND_DIST_DIR / "index.html").exists():
    app.mount(
        "/",
        SPAStaticFiles(directory=FRONTEND_DIST_DIR, html=True),
        name="frontend",
    )
