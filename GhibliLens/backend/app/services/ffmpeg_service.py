"""
FFmpeg Service – frame extraction, audio stripping, and final muxing.
"""
import subprocess
import json
from pathlib import Path
from typing import Optional
from app.models.schemas import VideoMetadata


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, capture_output=True, text=True, check=True
    )


def probe_video(video_path: Path) -> VideoMetadata:
    """Get video metadata via ffprobe."""
    result = _run([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", str(video_path)
    ])
    data = json.loads(result.stdout)

    video_stream = next(
        (s for s in data["streams"] if s["codec_type"] == "video"), None
    )
    audio_stream = next(
        (s for s in data["streams"] if s["codec_type"] == "audio"), None
    )

    if not video_stream:
        raise ValueError("No video stream found in file.")

    # Parse FPS (e.g. "24/1" or "30000/1001")
    fps_str = video_stream.get("r_frame_rate", "24/1")
    num, den = fps_str.split("/")
    fps = float(num) / float(den)

    duration = float(data["format"].get("duration", 0))

    return VideoMetadata(
        duration=duration,
        fps=round(fps, 2),
        width=int(video_stream["width"]),
        height=int(video_stream["height"]),
        has_audio=audio_stream is not None,
    )


def trim_video(
    input_path: Path,
    output_path: Path,
    start_time: float,
    end_time: float,
) -> None:
    """Trim a video to [start_time, end_time] with fast seek."""
    _run([
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-to", str(end_time),
        "-i", str(input_path),
        "-c", "copy",
        str(output_path),
    ])


def extract_frames(
    video_path: Path,
    frames_dir: Path,
    fps: int = 12,
) -> int:
    """Extract frames as PNG files. Returns frame count."""
    _run([
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vf", f"fps={fps}",
        "-q:v", "1",
        str(frames_dir / "frame_%05d.png"),
    ])
    return len(list(frames_dir.glob("frame_*.png")))


def extract_audio(video_path: Path, audio_path: Path) -> bool:
    """Strip audio track to AAC file. Returns True if audio existed."""
    try:
        _run([
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vn", "-acodec", "copy",
            str(audio_path),
        ])
        return True
    except subprocess.CalledProcessError:
        return False


def assemble_video(
    frames_dir: Path,
    output_path: Path,
    fps: int = 12,
    audio_path: Optional[Path] = None,
) -> None:
    """Reassemble stylized frames into MP4, optionally mux audio."""
    # Step 1: frames → silent MP4
    silent_path = output_path.parent / "silent.mp4"
    _run([
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        str(silent_path),
    ])

    # Step 2: mux audio if available
    if audio_path and audio_path.exists():
        _run([
            "ffmpeg", "-y",
            "-i", str(silent_path),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(output_path),
        ])
        silent_path.unlink(missing_ok=True)
    else:
        silent_path.rename(output_path)
