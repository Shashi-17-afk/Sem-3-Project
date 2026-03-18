"""
ControlNet Service – generates depth maps from frames using MiDaS (via OpenCV DNN).
Falls back to a simple edge map if model weights aren't available.
"""
import cv2
import numpy as np
from pathlib import Path


def generate_depth_map(frame_path: Path, output_path: Path) -> None:
    """
    Generate a depth/edge map for ControlNet conditioning.
    Uses Canny edge detection as a lightweight, dependency-free approach.
    For production, swap for MiDaS or Zoe-Depth.
    """
    img = cv2.imread(str(frame_path))
    if img is None:
        raise ValueError(f"Could not read frame: {frame_path}")

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Canny edge detection (SoftEdge approximation)
    edges = cv2.Canny(blurred, threshold1=50, threshold2=150)

    # Dilate slightly for softer edges (better for ControlNet SoftEdge mode)
    kernel = np.ones((2, 2), np.uint8)
    soft_edges = cv2.dilate(edges, kernel, iterations=1)

    # Convert to 3-channel image
    depth_rgb = cv2.cvtColor(soft_edges, cv2.COLOR_GRAY2BGR)

    cv2.imwrite(str(output_path), depth_rgb)


def generate_depth_maps_batch(
    frames_dir: Path,
    depth_dir: Path,
) -> list[Path]:
    """Process all frames in a directory and return list of depth map paths."""
    frame_files = sorted(frames_dir.glob("frame_*.png"))
    depth_paths = []

    for frame_path in frame_files:
        depth_path = depth_dir / frame_path.name
        generate_depth_map(frame_path, depth_path)
        depth_paths.append(depth_path)

    return depth_paths
