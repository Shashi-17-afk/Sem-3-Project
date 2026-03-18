import os
import shutil
import uuid
from pathlib import Path
from app.config import settings


def create_job_dirs(job_id: str) -> dict[str, Path]:
    """Create all working directories for a job."""
    base = Path(settings.temp_dir) / job_id
    dirs = {
        "base": base,
        "frames_in": base / "frames_in",
        "depth_maps": base / "depth_maps",
        "frames_out": base / "frames_out",
        "output": base / "output",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def cleanup_job(job_id: str) -> None:
    """Delete all temp files for a job."""
    base = Path(settings.temp_dir) / job_id
    if base.exists():
        shutil.rmtree(base, ignore_errors=True)


def new_job_id() -> str:
    return str(uuid.uuid4())


def get_output_path(job_id: str) -> Path:
    return Path(settings.temp_dir) / job_id / "output" / "output.mp4"


def output_exists(job_id: str) -> bool:
    return get_output_path(job_id).exists()
