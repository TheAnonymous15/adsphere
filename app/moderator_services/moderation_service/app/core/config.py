"""
AdSphere Moderation Service - Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Service
    APP_NAME: str = "AdSphere Moderation Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # CORS
    ALLOWED_ORIGINS: list = ["*"]  # Allow all origins for development

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5

    # Job processing
    JOB_TIMEOUT: int = 300  # 5 minutes
    MAX_CONCURRENT_JOBS: int = 10
    WORKER_COUNT: int = 4

    # Video processing
    MAX_VIDEO_SIZE_MB: int = 500  # Allow larger videos
    MAX_VIDEO_DURATION_SEC: int = 300  # 5 minutes max (300 frames at 2fps)
    FRAME_SAMPLE_FPS: float = 2.0  # 2 frames per second
    MAX_FRAMES_PER_VIDEO: int = 600  # Allow up to 600 frames for 5 min video

    # Model paths
    MODELS_DIR: str = "./models_weights"
    YOLO_VIOLENCE_MODEL: str = "yolov8n-violence.pt"
    YOLO_WEAPONS_MODEL: str = "yolov8n-weapons.pt"
    BLOOD_MODEL: str = "blood_cnn.pth"

    # GPU
    GPU_ENABLED: bool = False
    CUDA_DEVICE: int = 0

    # Thresholds (0.0-1.0)
    THRESHOLD_NUDITY_APPROVE: float = 0.2
    THRESHOLD_NUDITY_REVIEW: float = 0.4
    THRESHOLD_NUDITY_REJECT: float = 0.6

    THRESHOLD_SEXUAL_APPROVE: float = 0.15
    THRESHOLD_SEXUAL_REVIEW: float = 0.3
    THRESHOLD_SEXUAL_REJECT: float = 0.5

    THRESHOLD_VIOLENCE_APPROVE: float = 0.2
    THRESHOLD_VIOLENCE_REVIEW: float = 0.4
    THRESHOLD_VIOLENCE_REJECT: float = 0.6

    THRESHOLD_WEAPONS_APPROVE: float = 0.1
    THRESHOLD_WEAPONS_REVIEW: float = 0.3
    THRESHOLD_WEAPONS_REJECT: float = 0.5

    THRESHOLD_BLOOD_APPROVE: float = 0.1
    THRESHOLD_BLOOD_REVIEW: float = 0.3
    THRESHOLD_BLOOD_REJECT: float = 0.5

    THRESHOLD_HATE_APPROVE: float = 0.1
    THRESHOLD_HATE_REVIEW: float = 0.3
    THRESHOLD_HATE_REJECT: float = 0.5

    THRESHOLD_SELF_HARM_APPROVE: float = 0.05
    THRESHOLD_SELF_HARM_REVIEW: float = 0.15
    THRESHOLD_SELF_HARM_REJECT: float = 0.3

    # Logging
    LOG_DIR: str = "./logs"
    AUDIT_LOG_DIR: str = "./logs/audit"

    # Cache
    CACHE_DIR: str = "./cache"
    CACHE_TTL_SECONDS: int = 86400  # 24 hours

    # API Auth (optional)
    API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra env vars not in settings


settings = Settings()

