"""
Job Manager – tracks in-memory job state.
In production this would be backed by Redis.
"""
import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional
from app.models.schemas import JobStatus


@dataclass
class Job:
    job_id: str
    status: JobStatus = JobStatus.QUEUED
    progress: int = 0
    current_step: str = "Warming up the paintbrushes..."
    frames_done: int = 0
    frames_total: int = 0
    output_url: Optional[str] = None
    preview_frame_url: Optional[str] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)


# Global in-memory store
_jobs: dict[str, Job] = {}


def create_job(job_id: str) -> Job:
    job = Job(job_id=job_id)
    _jobs[job_id] = job
    return job


def get_job(job_id: str) -> Optional[Job]:
    return _jobs.get(job_id)


def update_job(
    job_id: str,
    *,
    status: Optional[JobStatus] = None,
    progress: Optional[int] = None,
    current_step: Optional[str] = None,
    frames_done: Optional[int] = None,
    frames_total: Optional[int] = None,
    output_url: Optional[str] = None,
    preview_frame_url: Optional[str] = None,
    error: Optional[str] = None,
) -> None:
    job = _jobs.get(job_id)
    if not job:
        return
    if status is not None:
        job.status = status
    if progress is not None:
        job.progress = progress
    if current_step is not None:
        job.current_step = current_step
    if frames_done is not None:
        job.frames_done = frames_done
    if frames_total is not None:
        job.frames_total = frames_total
    if output_url is not None:
        job.output_url = output_url
    if preview_frame_url is not None:
        job.preview_frame_url = preview_frame_url
    if error is not None:
        job.error = error


def delete_job(job_id: str) -> None:
    _jobs.pop(job_id, None)
