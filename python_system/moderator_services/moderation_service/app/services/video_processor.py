"""
Video processing service with ffmpeg
Handles frame extraction, audio extraction, and video analysis
"""
import os
import subprocess
import tempfile
import hashlib
import secrets
from pathlib import Path
from typing import List, Dict, Optional
import cv2
from app.core.config import settings


class VideoProcessor:
    """
    Video processing and frame extraction using ffmpeg and OpenCV.
    """

    def __init__(self):
        self.temp_base_dir = tempfile.gettempdir()

    @staticmethod
    def generate_secure_temp_dirname() -> str:
        """
        Generate a unique 256-bit cryptographic hex name for temp directory.

        Returns:
            64-character hex string (256 bits)
        """
        # Use secrets for cryptographically strong random bytes
        random_bytes = secrets.token_bytes(32)  # 32 bytes = 256 bits
        hex_name = random_bytes.hex()  # 64 hex characters
        return f"video_mod_{hex_name}"

    def create_secure_temp_dir(self) -> str:
        """
        Create a secure temporary directory with unique 256-bit hex name.

        Returns:
            Path to created temporary directory
        """
        dirname = self.generate_secure_temp_dirname()
        temp_path = os.path.join(self.temp_base_dir, dirname)
        os.makedirs(temp_path, exist_ok=True)
        return temp_path

    def extract_frames(
        self,
        video_path: str,
        output_dir: str,
        fps: Optional[float] = None,
        max_frames: Optional[int] = None
    ) -> List[str]:
        """
        Extract frames from video using ffmpeg.

        Args:
            video_path: Path to video file
            output_dir: Directory to save frames
            fps: Frames per second to extract (default: from config)
            max_frames: Maximum number of frames (default: from config)

        Returns:
            List of paths to extracted frames
        """
        fps = fps or settings.FRAME_SAMPLE_FPS
        max_frames = max_frames or settings.MAX_FRAMES_PER_VIDEO

        os.makedirs(output_dir, exist_ok=True)

        # Get video duration first
        duration = self._get_video_duration(video_path)
        if duration == 0:
            return []

        # Calculate actual fps to not exceed max_frames
        total_frames_at_fps = int(duration * fps)
        if total_frames_at_fps > max_frames:
            fps = max_frames / duration

        frame_pattern = os.path.join(output_dir, "frame_%05d.jpg")

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"fps={fps}",
            "-frames:v", str(max_frames),
            "-q:v", "2",  # Quality
            frame_pattern,
            "-loglevel", "error"
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"ffmpeg error: {e.stderr.decode()}")
            return []

        # Collect extracted frames
        frames = sorted(Path(output_dir).glob("frame_*.jpg"))
        return [str(f) for f in frames]

    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Extract audio track from video.

        Args:
            video_path: Path to video file
            output_path: Where to save audio (default: secure temp file)

        Returns:
            Path to extracted audio file (WAV format, 16kHz mono)
        """
        if output_path is None:
            # Generate secure filename
            secure_name = hashlib.sha256(
                f"{video_path}_{secrets.token_hex(16)}".encode()
            ).hexdigest()
            output_path = os.path.join(
                self.temp_base_dir,
                f"audio_{secure_name}.wav"
            )

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # PCM 16-bit
            "-ar", "16000",  # 16kHz sample rate
            "-ac", "1",  # Mono
            output_path,
            "-y",  # Overwrite
            "-loglevel", "error"
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"Audio extraction error: {e.stderr.decode()}")
            return None

    def get_video_info(self, video_path: str) -> Dict[str, any]:
        """
        Get video metadata using ffprobe.

        Returns:
            Dict with duration, width, height, fps, codec, etc.
        """
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            import json
            data = json.loads(result.stdout)

            video_stream = next(
                (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
                {}
            )

            format_info = data.get("format", {})

            return {
                "duration": float(format_info.get("duration", 0)),
                "size_bytes": int(format_info.get("size", 0)),
                "width": int(video_stream.get("width", 0)),
                "height": int(video_stream.get("height", 0)),
                "fps": eval(video_stream.get("r_frame_rate", "0/1")),
                "codec": video_stream.get("codec_name", "unknown"),
                "bitrate": int(format_info.get("bit_rate", 0)),
            }
        except Exception as e:
            print(f"ffprobe error: {e}")
            return {
                "duration": 0,
                "size_bytes": 0,
                "width": 0,
                "height": 0,
                "fps": 0,
                "codec": "unknown",
                "bitrate": 0,
            }

    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds"""
        info = self.get_video_info(video_path)
        return info.get("duration", 0)

    def validate_video(self, video_path: str) -> tuple[bool, str]:
        """
        Validate video meets requirements.

        Returns:
            (is_valid, error_message)
        """
        if not os.path.exists(video_path):
            return False, "Video file not found"

        info = self.get_video_info(video_path)

        # Check duration
        duration = info.get("duration", 0)
        if duration > settings.MAX_VIDEO_DURATION_SEC:
            return False, f"Video too long ({duration}s > {settings.MAX_VIDEO_DURATION_SEC}s)"

        # Check file size
        size_mb = info.get("size_bytes", 0) / (1024 * 1024)
        if size_mb > settings.MAX_VIDEO_SIZE_MB:
            return False, f"Video too large ({size_mb:.1f}MB > {settings.MAX_VIDEO_SIZE_MB}MB)"

        # Check resolution
        width = info.get("width", 0)
        height = info.get("height", 0)
        if width == 0 or height == 0:
            return False, "Invalid video resolution"

        return True, ""

    def create_thumbnail(self, video_path: str, output_path: str, timestamp: float = 1.0) -> bool:
        """
        Create thumbnail from video at specific timestamp.

        Args:
            video_path: Path to video
            output_path: Where to save thumbnail
            timestamp: Time in seconds to capture

        Returns:
            True if successful
        """
        cmd = [
            "ffmpeg",
            "-ss", str(timestamp),
            "-i", video_path,
            "-frames:v", "1",
            "-q:v", "2",
            output_path,
            "-y",
            "-loglevel", "error"
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

