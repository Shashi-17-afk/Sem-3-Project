"""
Jobs Router – polling, download, preview, cancel.
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings
from app.models.schemas import JobStatus, JobStatusResponse
from app.services import job_manager
from app.utils.file_utils import cleanup_job

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


def _get_job_or_404(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return job


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Poll the current status of a stylization job."""
    job = _get_job_or_404(job_id)
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        current_step=job.current_step,
        frames_done=job.frames_done,
        frames_total=job.frames_total,
        output_url=job.output_url,
        preview_frame_url=job.preview_frame_url,
        error=job.error,
    )


@router.get("/{job_id}/download")
async def download_result(job_id: str):
    """Download the final stylized MP4."""
    job = _get_job_or_404(job_id)
    if job.status != JobStatus.COMPLETE:
        raise HTTPException(
            status_code=425,
            detail=f"Job not complete yet. Current status: {job.status}",
        )
    output_path = Path(settings.temp_dir) / job_id / "output" / "output.mp4"
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output file not found.")

    return FileResponse(
        path=str(output_path),
        media_type="video/mp4",
        filename="ghiblilens_output.mp4",
    )


@router.get("/{job_id}/preview")
async def get_preview_frame(job_id: str):
    """Return a preview still frame (JPEG) for the comparison player."""
    job = _get_job_or_404(job_id)
    preview_path = Path(settings.temp_dir) / job_id / "output" / "preview.png"
    if not preview_path.exists():
        raise HTTPException(status_code=404, detail="Preview not ready yet.")

    return FileResponse(path=str(preview_path), media_type="image/png")


@router.delete("/{job_id}", status_code=204)
async def cancel_job(job_id: str):
    """Cancel a job and clean up its temp files."""
    _get_job_or_404(job_id)
    job_manager.delete_job(job_id)
    cleanup_job(job_id)
