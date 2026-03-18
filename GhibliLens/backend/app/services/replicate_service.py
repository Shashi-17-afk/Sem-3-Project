"""
Replicate Service – sends frames to SDXL + Ghibli LoRA via Replicate API.
"""
import os
import base64
import httpx
from pathlib import Path
from PIL import Image
import replicate
from app.config import settings


def _image_to_data_uri(image_path: Path) -> str:
    """Convert an image file to a base64 data URI for Replicate."""
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    ext = image_path.suffix.lstrip(".")
    mime = "image/png" if ext == "png" else f"image/{ext}"
    return f"data:{mime};base64,{data}"


async def stylize_frame(
    frame_path: Path,
    depth_map_path: Path,
    output_path: Path,
) -> None:
    """
    Run a single frame through SDXL + ControlNet (depth) on Replicate.
    Saves the result to output_path.
    """
    os.environ["REPLICATE_API_TOKEN"] = settings.replicate_api_token

    # Open the original frame to get dimensions
    with Image.open(frame_path) as img:
        width, height = img.size

    # Snap to multiples of 8 (required by diffusion models)
    width = (width // 8) * 8
    height = (height // 8) * 8

    input_payload = {
        "prompt": settings.ghibli_prompt,
        "negative_prompt": settings.negative_prompt,
        "image": _image_to_data_uri(frame_path),
        "control_image": _image_to_data_uri(depth_map_path),
        "controlnet_conditioning_scale": settings.controlnet_conditioning_scale,
        "num_inference_steps": settings.inference_steps,
        "guidance_scale": settings.guidance_scale,
        "width": width,
        "height": height,
        "scheduler": "K_EULER",
    }

    output = replicate.run(settings.replicate_model, input=input_payload)

    # `output` is a list of file URLs or a single URL
    result_url = output[0] if isinstance(output, list) else output

    async with httpx.AsyncClient() as client:
        response = await client.get(str(result_url))
        response.raise_for_status()
        output_path.write_bytes(response.content)
