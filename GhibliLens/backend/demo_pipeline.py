"""
GhibliLens Full Demo Runner
============================
Runs the COMPLETE pipeline on a real video:
  1. FFmpeg  → extract frames + strip audio
  2. ControlNet → SoftEdge map per frame
  3. Ghibli Filter → CPU-based Ghibli-style colour + edge overlay
     (replaces Replicate API when billing isn't set up yet)
  4. Temporal consistency → optical flow blend
  5. FFmpeg → reassemble frames + mux original audio

Usage:
  .venv\Scripts\python.exe demo_pipeline.py --video demo_input.mp4
"""

import argparse
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

# ── Add project root to path ──────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from app.services.ffmpeg_service import (
    assemble_video,
    extract_audio,
    extract_frames,
    probe_video,
)
from app.services.controlnet_service import generate_depth_map
from app.services.consistency_service import apply_optical_flow_blend


# ─────────────────────────────────────────────────────────
# Ghibli-style CPU filter
# Uses: bilateral smoothing, colour shift, edge overlay
# ─────────────────────────────────────────────────────────
def ghibli_filter(frame_path: Path, output_path: Path) -> None:
    img = cv2.imread(str(frame_path))
    if img is None:
        shutil.copy(frame_path, output_path)
        return

    # 1. Bilateral filter × 3  (cartoon-smooth skin / nature)
    result = img.copy()
    for _ in range(3):
        result = cv2.bilateralFilter(result, d=9, sigmaColor=75, sigmaSpace=75)

    # 2. Ghibli colour grading – boost greens & blues, warm shadows
    hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV).astype(np.float32)
    # Shift hue slightly toward green (Ghibli lush nature palette)
    hsv[:, :, 0] = np.clip(hsv[:, :, 0] + 3, 0, 179)
    # Boost saturation for watercolour vibrancy
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.35, 0, 255)
    # Slightly brighten midtones
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.08, 0, 255)
    result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    # 3. Soft edge overlay (hand-drawn ink lines effect)
    gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    edges = cv2.Laplacian(blurred, cv2.CV_64F)
    edges = np.clip(np.abs(edges), 0, 80).astype(np.uint8)
    edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    result = cv2.subtract(result, edges_bgr)

    # 4. Soft vignette (painterly frame)
    rows, cols = result.shape[:2]
    X, Y = np.meshgrid(np.linspace(-1, 1, cols), np.linspace(-1, 1, rows))
    vignette = np.clip(1 - 0.4 * (X**2 + Y**2), 0.6, 1.0)
    result = (result * vignette[:, :, np.newaxis]).astype(np.uint8)

    cv2.imwrite(str(output_path), result)


def run_demo(video_path: Path) -> None:
    print(f"\n🌿 GhibliLens Demo Pipeline")
    print(f"   Input  : {video_path}")

    out_base = Path("demo_output")
    dirs = {
        "frames_in":   out_base / "frames_in",
        "depth_maps":  out_base / "depth_maps",
        "frames_ghibli": out_base / "frames_ghibli",
        "frames_final":  out_base / "frames_final",
        "output":      out_base / "output",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    # ── 1. Probe + extract audio ──────────────────────────
    print("\n[1/5] Probing video...")
    meta = probe_video(video_path)
    print(f"      Duration: {meta.duration:.1f}s  |  {meta.width}×{meta.height}  |  {meta.fps} fps")

    audio_path = out_base / "audio.aac"
    if meta.has_audio:
        extract_audio(video_path, audio_path)
        print(f"      Audio stripped → {audio_path}")

    # ── 2. Extract frames ─────────────────────────────────
    print("\n[2/5] Extracting frames at 12 fps...")
    total = extract_frames(video_path, dirs["frames_in"], fps=12)
    print(f"      ✅ {total} frames extracted")

    # ── 3. ControlNet edge maps ───────────────────────────
    print("\n[3/5] Generating ControlNet edge maps...")
    frame_files = sorted(dirs["frames_in"].glob("frame_*.png"))
    for f in frame_files:
        generate_depth_map(f, dirs["depth_maps"] / f.name)
    print(f"      ✅ {len(frame_files)} edge maps generated")

    # ── 4. Ghibli CPU filter ──────────────────────────────
    print("\n[4/5] Applying Ghibli-style filter to every frame...")
    print("      (Replicate API would run here once billing is added)")
    for i, f in enumerate(frame_files):
        ghibli_filter(f, dirs["frames_ghibli"] / f.name)
        pct = int((i + 1) / len(frame_files) * 100)
        print(f"      Frame {i+1:3}/{len(frame_files)}  [{pct:3}%]", end="\r")
    print(f"      ✅ {len(frame_files)} frames stylized              ")

    # ── 5. Temporal consistency ───────────────────────────
    print("\n[5/5] Applying temporal consistency (optical flow)...")
    ghibli_frames = sorted(dirs["frames_ghibli"].glob("frame_*.png"))
    shutil.copy(ghibli_frames[0], dirs["frames_final"] / ghibli_frames[0].name)
    for i in range(1, len(ghibli_frames)):
        prev_out = dirs["frames_final"] / ghibli_frames[i - 1].name
        curr_in  = ghibli_frames[i]
        curr_out = dirs["frames_final"] / ghibli_frames[i].name
        apply_optical_flow_blend(prev_out, curr_in, curr_out, alpha=0.25)
    print(f"      ✅ Temporal smoothing applied")

    # ── 6. Assemble final MP4 ────────────────────────────
    print("\n[6/5] Assembling final Ghibli MP4...")
    output_mp4 = dirs["output"] / "ghiblilens_demo.mp4"
    assemble_video(
        dirs["frames_final"],
        output_mp4,
        fps=12,
        audio_path=audio_path if meta.has_audio and audio_path.exists() else None,
    )

    size_mb = output_mp4.stat().st_size / 1024 / 1024
    print(f"\n✅ Done! Output → {output_mp4.resolve()}")
    print(f"   File size : {size_mb:.2f} MB")
    print(f"   Frames    : {len(frame_files)}")
    print(f"\n   Open the file to see your Ghibli-style video! 🌿\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="Path to input MP4")
    args = parser.parse_args()
    run_demo(Path(args.video))
