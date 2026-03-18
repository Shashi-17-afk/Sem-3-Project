import os
from fastapi import HTTPException, UploadFile
from app.config import settings
from app.models.schemas import VideoMetadata

ALLOWED_TYPES = {"video/mp4", "video/quicktime", "video/webm", "video/x-msvideo"}
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".webm", ".avi"}


def validate_video_file(file: UploadFile) -> None:
    """Validate file type and content type."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )


def validate_trim_range(start_time: float, end_time: float, duration: float) -> None:
    """Validate trim start/end are within bounds and ≤ 15s."""
    if start_time < 0:
        raise HTTPException(status_code=422, detail="start_time cannot be negative.")
    if end_time > duration:
        raise HTTPException(
            status_code=422,
            detail=f"end_time ({end_time}s) exceeds video duration ({duration:.1f}s).",
        )
    if start_time >= end_time:
        raise HTTPException(
            status_code=422, detail="start_time must be less than end_time."
        )
    segment_duration = end_time - start_time
    if segment_duration > settings.max_video_duration:
        raise HTTPException(
            status_code=422,
            detail=f"Selected segment is {segment_duration:.1f}s. Max allowed is {settings.max_video_duration}s.",
        )
