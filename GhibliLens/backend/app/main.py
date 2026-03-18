from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path

from app.config import settings
from app.routers import video, jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure temp directory exists on startup
    Path(settings.temp_dir).mkdir(exist_ok=True)
    yield
    # Cleanup on shutdown (optional)


app = FastAPI(
    title="GhibliLens API",
    description="Convert your videos into Studio Ghibli anime style using AI.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(video.router)
app.include_router(jobs.router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "GhibliLens API"}


# ── Production: serve the built React app ──────────────────
# In Docker the frontend is built into /app/static by the
# multi-stage Dockerfile. In local dev this dir won't exist
# so we skip mounting it (Vite dev server handles it instead).
_STATIC_DIR = Path(__file__).parent.parent / "static"

if _STATIC_DIR.exists():
    # Serve JS/CSS/assets
    app.mount("/assets", StaticFiles(directory=str(_STATIC_DIR / "assets")), name="assets")

    # SPA catch-all: every unknown path returns index.html so
    # client-side React Router routes work correctly.
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        index = _STATIC_DIR / "index.html"
        return FileResponse(str(index))
