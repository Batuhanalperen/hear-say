# Multi-stage build:
#   Stage 1: Nuxt frontend (Node 22)
#   Stage 2: Python backend with CUDA runtime + pre-downloaded model weights

# ---- Stage 1: Frontend ----
FROM node:22-alpine AS frontend-builder

WORKDIR /build

RUN corepack enable && corepack prepare pnpm@10.25.0 --activate
ENV PNPM_HOME=/pnpm
RUN pnpm config set store-dir /pnpm/store

COPY frontend/package.json frontend/pnpm-lock.yaml frontend/.npmrc ./
RUN --mount=type=cache,id=pnpm-store,target=/pnpm/store \
    pnpm install --frozen-lockfile

COPY frontend/ ./
RUN --mount=type=cache,id=pnpm-store,target=/pnpm/store \
    pnpm build

# ---- Stage 2: Backend with CUDA ----
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONIOENCODING=utf-8 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_RETRIES=10 \
    PIP_DEFAULT_TIMEOUT=180

# System deps:
#   Python 3.10, ffmpeg, libsndfile — audio IO
#   wget — piano_transcription_inference downloads weights with wget
#   curl, ca-certificates — healthcheck + HTTPS
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.10 \
        python3.10-dev \
        python3.10-venv \
        python3-pip \
        ffmpeg \
        libsndfile1 \
        ca-certificates \
        curl \
        wget \
    && ln -sf /usr/bin/python3.10 /usr/local/bin/python \
    && ln -sf /usr/bin/python3.10 /usr/local/bin/python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Ubuntu 22.04 ships an old pip; upgrade so modern flags and wheels work
RUN --mount=type=cache,id=pip,target=/root/.cache/pip \
    python3 -m pip install --upgrade pip setuptools wheel

# PyTorch CUDA 12.1 wheels (large download; dedicated layer for caching)
RUN --mount=type=cache,id=pip,target=/root/.cache/pip \
    pip install torch torchaudio torchvision \
        --index-url https://download.pytorch.org/whl/cu121

COPY backend/pyproject.toml ./
COPY backend/hear_say ./hear_say

# Pin the CUDA torch trio so transitive deps (e.g. onnx2torch -> torchvision)
# cannot pull a newer CPU/PyPI torch that breaks torchaudio's native lib.
RUN --mount=type=cache,id=pip,target=/root/.cache/pip \
    pip freeze | grep -E '^torch(audio|vision)?==' > /tmp/torch-constraints.txt \
    && pip install -e ".[backend]" -c /tmp/torch-constraints.txt

# Pre-download model weights at build time so the first request does not wait.
# device='cpu' lets us initialise on build machines without a GPU; weights are
# later loaded onto CUDA at runtime.
RUN python3 -c "from piano_transcription_inference import PianoTranscription; PianoTranscription(device='cpu')" \
    && ls -lh /root/piano_transcription_inference_data/

# BS-Roformer weights (~200 MB). Fail-soft: if network is flaky we fall back to
# a runtime download instead of breaking the build.
RUN python3 -c "from audio_separator.separator import Separator; s = Separator(); s.load_model(model_filename='model_bs_roformer_ep_317_sdr_12.9755.ckpt')" \
    || echo "[warn] BS-Roformer pre-download failed; runtime download will be used"

# Frontend static files from stage 1
COPY --from=frontend-builder /build/.output/public /app/frontend_dist

RUN mkdir -p /data

ENV HEAR_SAY_DATA_DIR=/data \
    HEAR_SAY_FRONTEND_DIST=/app/frontend_dist \
    HEAR_SAY_DEVICE=cuda

EXPOSE 7777

HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD curl -fsS http://localhost:7777/api/health || exit 1

CMD ["python3", "-m", "uvicorn", "hear_say.main:app", "--host", "0.0.0.0", "--port", "7777"]
