"""
Video Upload & Stylization Router
POST /api/v1/video/upload
"""
import asyncio
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import settings
from app.models.schemas import JobStatus, UploadResponse
from app.services import job_manager
from app.services.controlnet_service import generate_depth_maps_batch
from app.services.consistency_service import apply_consistency_pass
from app.services.ffmpeg_service import (
    assemble_video,
    extract_audio,
    extract_frames,
    probe_video,
    trim_video,
)
from app.services.replicate_service import stylize_frame
from app.utils.file_utils import cleanup_job, create_job_dirs, new_job_id, get_output_path
from app.utils.validators import validate_trim_range, validate_video_file

router = APIRouter(prefix="/api/v1/video", tags=["video"])

# Cheeky progress messages shown in the UI
PROGRESS_MESSAGES = [
    "Warming up the paintbrushes...",
    "Mixing the watercolors...",
    "Sketching the scenery...",
    "Adding the forest spirits...",
    "Painting the sky...",
    "Bringing Totoro to life...",
    "Polishing every frame...",
    "Almost there – just a touch of magic...",
]


async def _run_pipeline(
    job_id: str,
    video_path: Path,
    dirs: dict,
    fps: int,
    has_audio: bool,
) -> None:
    """The full stylization pipeline, runs as a background task."""
    try:
        job_manager.update_job(
            job_id,
            status=JobStatus.PROCESSING,
            current_step=PROGRESS_MESSAGES[0],
        )

        # 1. Extract audio
        audio_path = dirs["base"] / "audio.aac"
        if has_audio:
            extract_audio(video_path, audio_path)

        # 2. Extract frames
        job_manager.update_job(job_id, current_step=PROGRESS_MESSAGES[1])
        total_frames = extract_frames(video_path, dirs["frames_in"], fps=fps)
        job_manager.update_job(job_id, frames_total=total_frames)

        # 3. Generate depth/edge maps (ControlNet conditioning)
        job_manager.update_job(job_id, current_step=PROGRESS_MESSAGES[2])
        generate_depth_maps_batch(dirs["frames_in"], dirs["depth_maps"])

        # 4. Stylize each frame via Replicate
        frame_paths = sorted(dirs["frames_in"].glob("frame_*.png"))
        stylized_dir = dirs["frames_out"]

        for i, frame_path in enumerate(frame_paths):
            depth_path = dirs["depth_maps"] / frame_path.name
            out_path = stylized_dir / frame_path.name

            msg_idx = min(3 + (i * 4 // total_frames), len(PROGRESS_MESSAGES) - 1)
            job_manager.update_job(
                job_id,
                current_step=PROGRESS_MESSAGES[msg_idx],
                frames_done=i + 1,
                progress=int(10 + 70 * (i + 1) / total_frames),
            )
            await stylize_frame(frame_path, depth_path, out_path)

        # 5. Temporal consistency pass (reduce flickering)
        job_manager.update_job(
            job_id,
            current_step=PROGRESS_MESSAGES[6],
            progress=85,
        )
        consistent_dir = dirs["base"] / "frames_consistent"
        consistent_dir.mkdir(exist_ok=True)
        apply_consistency_pass(stylized_dir, consistent_dir)

        # 6. Save preview frame (first frame of output)
        preview_frames = sorted(consistent_dir.glob("frame_*.png"))
        if preview_frames:
            shutil.copy(preview_frames[0], dirs["output"] / "preview.png")

        # 7. Assemble final MP4
        job_manager.update_job(
            job_id,
            current_step=PROGRESS_MESSAGES[7],
            progress=95,
        )
        output_path = dirs["output"] / "output.mp4"
        assemble_video(
            consistent_dir,
            output_path,
            fps=fps,
            audio_path=audio_path if has_audio else None,
        )

        job_manager.update_job(
            job_id,
            status=JobStatus.COMPLETE,
            progress=100,
            current_step="Done! Your Ghibli world awaits. 🌿",
            output_url=f"/api/v1/jobs/{job_id}/download",
            preview_frame_url=f"/api/v1/jobs/{job_id}/preview",
        )

    except Exception as e:
        job_manager.update_job(
            job_id,
            status=JobStatus.FAILED,
            error=str(e),
            current_step=f"Something went wrong: {e}",
        )


@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    start_time: float = Form(default=0.0),
    end_time: Optional[float] = Form(default=None),
    fps: int = Form(default=12),
    style_strength: float = Form(default=0.75),
):
    """Upload a video and kick off Ghibli stylization."""
    validate_video_file(file)

    if fps not in (12, 24):
        raise HTTPException(status_code=422, detail="fps must be 12 or 24.")

    # Save upload to temp location
    job_id = new_job_id()
    dirs = create_job_dirs(job_id)
    raw_suffix = Path(file.filename or "video.mp4").suffix
    raw_path = dirs["base"] / f"raw{raw_suffix}"

    with open(raw_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Probe the file
    meta = probe_video(raw_path)
    requires_trim = meta.duration > settings.max_video_duration

    # Determine trim window
    resolved_end = end_time if end_time is not None else min(meta.duration, settings.max_video_duration)
    validate_trim_range(start_time, resolved_end, meta.duration)

    # Trim if needed
    if requires_trim or start_time > 0 or resolved_end < meta.duration:
        trimmed_path = dirs["base"] / f"trimmed{raw_suffix}"
        trim_video(raw_path, trimmed_path, start_time, resolved_end)
        process_path = trimmed_path
    else:
        process_path = raw_path

    # Register job
    job_manager.create_job(job_id)

    # Launch background task
    background_tasks.add_task(
        _run_pipeline,
        job_id,
        process_path,
        dirs,
        fps,
        meta.has_audio,
    )

    return UploadResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        message="Your Ghibli transformation has begun! 🎨",
        estimated_seconds=int(meta.duration * 6),  # ~6s per second of video
        poll_url=f"/api/v1/jobs/{job_id}/status",
        requires_trim=requires_trim,
        video_duration=meta.duration,
    )
