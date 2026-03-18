"""
Temporal Consistency Service – reduces flickering between stylized frames.
Uses Farneback Optical Flow to warp the previous frame and blend it into the current.
"""
import cv2
import numpy as np
from pathlib import Path


def apply_optical_flow_blend(
    prev_frame_path: Path,
    curr_frame_path: Path,
    output_path: Path,
    alpha: float = 0.3,
) -> None:
    """
    Blend `curr_frame` with a warped version of `prev_frame` using optical flow.
    alpha=0.3 means 30% of the prev (warped) frame is mixed in.
    Lower alpha = less temporal blending, higher = smoother but ghosting risk.
    """
    prev = cv2.imread(str(prev_frame_path)).astype(np.float32)
    curr = cv2.imread(str(curr_frame_path)).astype(np.float32)

    if prev.shape != curr.shape:
        prev = cv2.resize(prev, (curr.shape[1], curr.shape[0]))

    # Compute optical flow on grayscale
    prev_gray = cv2.cvtColor(prev.astype(np.uint8), cv2.COLOR_BGR2GRAY)
    curr_gray = cv2.cvtColor(curr.astype(np.uint8), cv2.COLOR_BGR2GRAY)

    flow = cv2.calcOpticalFlowFarneback(
        prev_gray, curr_gray,
        None,
        pyr_scale=0.5,
        levels=3,
        winsize=15,
        iterations=3,
        poly_n=5,
        poly_sigma=1.2,
        flags=0,
    )

    # Build remap grid
    h, w = flow.shape[:2]
    map_x = np.tile(np.arange(w), (h, 1)).astype(np.float32) + flow[..., 0]
    map_y = np.tile(np.arange(h), (w, 1)).T.astype(np.float32) + flow[..., 1]

    # Warp previous frame toward current
    warped_prev = cv2.remap(prev, map_x, map_y, interpolation=cv2.INTER_LINEAR)

    # Alpha blend: (1 - alpha) * curr + alpha * warped_prev
    blended = cv2.addWeighted(curr, 1.0 - alpha, warped_prev, alpha, 0)

    cv2.imwrite(str(output_path), blended.astype(np.uint8))


def apply_consistency_pass(
    frames_dir: Path,
    output_dir: Path,
    alpha: float = 0.3,
) -> None:
    """Apply temporal blending across all stylized frames in order."""
    frame_paths = sorted(frames_dir.glob("frame_*.png"))

    if not frame_paths:
        return

    # First frame: no previous, just copy
    import shutil
    shutil.copy(frame_paths[0], output_dir / frame_paths[0].name)

    # Remaining frames: blend with previous output
    for i in range(1, len(frame_paths)):
        prev_output = output_dir / frame_paths[i - 1].name
        curr_input = frame_paths[i]
        curr_output = output_dir / frame_paths[i].name

        apply_optical_flow_blend(prev_output, curr_input, curr_output, alpha=alpha)
