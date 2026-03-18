from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Replicate API
    replicate_api_token: str = ""

    # Model settings
    replicate_model: str = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
    ghibli_prompt: str = (
        "Studio Ghibli style, lush watercolor textures, hand-painted backgrounds, "
        "soft lighting, high-quality anime, Miyazaki aesthetic, cel shading, "
        "vibrant nature, whimsical atmosphere"
    )
    negative_prompt: str = (
        "photorealistic, 3D render, ugly, blurry, low quality, "
        "noise, artifacts, deformed, disfigured"
    )
    controlnet_conditioning_scale: float = 0.75
    inference_steps: int = 30
    guidance_scale: float = 7.5

    # Video settings
    max_video_duration: int = 15   # seconds
    default_fps: int = 12
    max_fps: int = 24
    max_file_size_mb: int = 100

    # Job settings
    job_expiry_seconds: int = 3600  # 1 hour

    # Paths
    temp_dir: str = "temp_jobs"

    # Server
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
