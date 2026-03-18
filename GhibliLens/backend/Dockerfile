# ── Stage 1: Build React frontend ─────────────────────────
FROM node:22-alpine AS frontend-builder

WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python backend + FFmpeg ─────────────────────
FROM python:3.11-slim

# Install ffmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install Python deps
COPY backend/pyproject.toml backend/uv.lock* ./
RUN uv sync --no-install-project --frozen || uv sync --no-install-project

# Copy backend source
COPY backend/app ./app

# Copy built frontend into static folder
COPY --from=frontend-builder /build/frontend/dist ./static

# Serve frontend as static files via FastAPI
ENV PYTHONUNBUFFERED=1
ENV TEMP_DIR=/tmp/jobs

# Cloud Run uses PORT env var
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
