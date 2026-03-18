from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class UploadResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str
    estimated_seconds: int
    poll_url: str
    requires_trim: bool = False
    video_duration: Optional[float] = None


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    current_step: str
    frames_done: int = 0
    frames_total: int = 0
    output_url: Optional[str] = None
    preview_frame_url: Optional[str] = None
    error: Optional[str] = None


class VideoMetadata(BaseModel):
    duration: float
    fps: float
    width: int
    height: int
    has_audio: bool
