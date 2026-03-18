"""
Step 2 Validation Script – Test the full AI pipeline on a single frame.

Run from the backend/ directory:
    .venv\Scripts\python.exe test_pipeline.py --image path\to\any\image.png

This validates:
    1. ControlNet depth map generation (no API needed)
    2. Replicate API call with the Ghibli prompt (needs REPLICATE_API_TOKEN in .env)
    3. Temporal consistency blend between two frames (no API needed)
"""

import argparse
import shutil
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from app.config import settings


def test_controlnet(image_path: Path, out_dir: Path) -> Path:
    """Test 1: depth/edge map generation."""
    print("\n[1/3] Testing ControlNet edge map generation...")
    from app.services.controlnet_service import generate_depth_map
    depth_out = out_dir / "depth_map.png"
    generate_depth_map(image_path, depth_out)
    print(f"      ✅ Depth map saved → {depth_out}")
    return depth_out


def test_replicate(frame_path: Path, depth_path: Path, out_dir: Path) -> Path:
    """Test 2: single-frame Replicate stylization."""
    print("\n[2/3] Testing Replicate API (Ghibli stylization)...")
    if not settings.replicate_api_token or settings.replicate_api_token == "your_replicate_api_token_here":
        print("      ⚠️  REPLICATE_API_TOKEN not set in .env — skipping this test.")
        print("          Get your token at: https://replicate.com/account/api-tokens")
        return frame_path
    
    import asyncio
    from app.services.replicate_service import stylize_frame
    stylized_out = out_dir / "stylized_frame.png"
    asyncio.run(stylize_frame(frame_path, depth_path, stylized_out))
    print(f"      ✅ Stylized frame saved → {stylized_out}")
    return stylized_out


def test_consistency(frame1: Path, frame2: Path, out_dir: Path) -> None:
    """Test 3: optical flow temporal blend."""
    print("\n[3/3] Testing temporal consistency (optical flow blend)...")
    from app.services.consistency_service import apply_optical_flow_blend
    blended_out = out_dir / "blended_frame.png"
    apply_optical_flow_blend(frame1, frame2, blended_out, alpha=0.3)
    print(f"      ✅ Blended frame saved → {blended_out}")


def main():
    parser = argparse.ArgumentParser(description="GhibliLens pipeline test")
    parser.add_argument(
        "--image",
        required=True,
        help="Path to a source image (PNG/JPG) to use as a test frame",
    )
    args = parser.parse_args()

    source = Path(args.image)
    if not source.exists():
        print(f"❌ Image not found: {source}")
        sys.exit(1)

    out_dir = Path("test_output")
    out_dir.mkdir(exist_ok=True)

    # Copy source as frame_00001.png
    frame1 = out_dir / "frame_00001.png"
    shutil.copy(source, frame1)

    print(f"\n🎨 GhibliLens Pipeline Test")
    print(f"   Source image : {source}")
    print(f"   Output dir   : {out_dir.resolve()}")

    depth_path = test_controlnet(frame1, out_dir)
    stylized = test_replicate(frame1, depth_path, out_dir)
    test_consistency(frame1, stylized, out_dir)

    print(f"\n✅ All tests complete! Results in: {out_dir.resolve()}")
    print(f"   Open the output folder to inspect the generated images.\n")


if __name__ == "__main__":
    main()
