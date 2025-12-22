"""
Video/Audio Separator - First Touchpoint for Video Moderation
Separates video stream from audio stream for parallel processing

This is the ENTRY POINT for all video moderation.
"""
import os
import subprocess
import secrets
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from app.core.config import settings


@dataclass
class SeparationResult:
    """Result of video/audio separation"""
    success: bool
    video_path: Optional[str]  # Path to video-only file (no audio)
    audio_path: Optional[str]  # Path to extracted audio (WAV)
    temp_dir: str              # Secure temp directory
    original_path: str         # Original video path
    has_audio: bool            # Whether video had audio track
    duration: float            # Video duration in seconds
    error: Optional[str] = None
    metadata: Dict = None


class VideoAudioSeparator:
    """
    First touchpoint for video moderation.

    Responsibilities:
    1. Validate incoming video file
    2. Create secure temporary directory
    3. Extract audio track to WAV (16kHz mono for ASR)
    4. Create video-only version (optional, for frame extraction)
    5. Return paths for parallel processing

    Flow:
        Video Upload → VideoAudioSeparator →
            ├── Audio → audio_processor.py (ASR + toxicity)
            └── Video → extract_video_frames.py → video_frame_processor.py
    """

    def __init__(self):
        self.temp_base_dir = tempfile.gettempdir()
        self.supported_formats = ['.mp4', '.webm', '.mov', '.avi', '.mkv', '.m4v', '.flv']

    @staticmethod
    def generate_secure_dirname() -> str:
        """Generate cryptographically secure 256-bit hex directory name."""
        random_bytes = secrets.token_bytes(32)  # 256 bits
        return f"mod_video_{random_bytes.hex()}"

    def create_secure_temp_dir(self) -> str:
        """Create secure temporary directory with unique name."""
        dirname = self.generate_secure_dirname()
        temp_path = os.path.join(self.temp_base_dir, dirname)
        os.makedirs(temp_path, exist_ok=True)

        # Create subdirectories
        os.makedirs(os.path.join(temp_path, "audio"), exist_ok=True)
        os.makedirs(os.path.join(temp_path, "frames"), exist_ok=True)

        return temp_path

    def validate_video(self, video_path: str) -> Tuple[bool, str, Dict]:
        """Validate video file before processing."""
        # Check file exists
        if not os.path.exists(video_path):
            return False, f"Video file not found: {video_path}", {}

        # Check file extension
        ext = Path(video_path).suffix.lower()
        if ext not in self.supported_formats:
            return False, f"Unsupported format: {ext}. Supported: {', '.join(self.supported_formats)}", {}

        # Get video metadata using ffprobe
        metadata = self._get_video_metadata(video_path)

        if metadata.get('duration', 0) == 0:
            return False, "Could not determine video duration - file may be corrupted", metadata

        # Check duration limit
        if metadata['duration'] > settings.MAX_VIDEO_DURATION_SEC:
            return False, f"Video too long: {metadata['duration']:.1f}s > {settings.MAX_VIDEO_DURATION_SEC}s max", metadata

        # Check file size
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        if file_size_mb > settings.MAX_VIDEO_SIZE_MB:
            return False, f"Video too large: {file_size_mb:.1f}MB > {settings.MAX_VIDEO_SIZE_MB}MB max", metadata

        metadata['file_size_mb'] = file_size_mb

        return True, "", metadata

    def _get_video_metadata(self, video_path: str) -> Dict:
        """Extract video metadata using ffprobe."""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            import json
            data = json.loads(result.stdout)

            # Find video stream
            video_stream = next(
                (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
                {}
            )

            # Find audio stream
            audio_stream = next(
                (s for s in data.get("streams", []) if s.get("codec_type") == "audio"),
                None
            )

            format_info = data.get("format", {})

            # Parse frame rate
            fps_str = video_stream.get("r_frame_rate", "0/1")
            try:
                if '/' in fps_str:
                    num, den = fps_str.split('/')
                    fps = float(num) / float(den) if float(den) != 0 else 0
                else:
                    fps = float(fps_str)
            except:
                fps = 0

            return {
                "duration": float(format_info.get("duration", 0)),
                "width": int(video_stream.get("width", 0)),
                "height": int(video_stream.get("height", 0)),
                "fps": fps,
                "video_codec": video_stream.get("codec_name", "unknown"),
                "has_audio": audio_stream is not None,
                "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
                "bitrate": int(format_info.get("bit_rate", 0)),
                "format_name": format_info.get("format_name", "unknown")
            }

        except subprocess.TimeoutExpired:
            return {"duration": 0, "error": "ffprobe timeout"}
        except Exception as e:
            return {"duration": 0, "error": str(e)}

    def separate(self, video_path: str) -> SeparationResult:
        """
        Main entry point: Separate video and audio tracks.

        Args:
            video_path: Path to input video file

        Returns:
            SeparationResult with paths to separated streams
        """
        # Step 1: Validate video
        is_valid, error_msg, metadata = self.validate_video(video_path)

        if not is_valid:
            return SeparationResult(
                success=False,
                video_path=None,
                audio_path=None,
                temp_dir="",
                original_path=video_path,
                has_audio=False,
                duration=0,
                error=error_msg,
                metadata=metadata
            )

        # Step 2: Create secure temp directory
        temp_dir = self.create_secure_temp_dir()

        try:
            # Step 3: Extract audio track
            audio_path = None
            has_audio = metadata.get('has_audio', False)

            if has_audio:
                audio_path = self._extract_audio(video_path, temp_dir)
                if audio_path is None:
                    print(f"⚠ Audio extraction failed, continuing without audio")
                    has_audio = False

            # Step 4: Video path remains the original (frames will be extracted from it)
            return SeparationResult(
                success=True,
                video_path=video_path,  # Use original for frame extraction
                audio_path=audio_path,
                temp_dir=temp_dir,
                original_path=video_path,
                has_audio=has_audio and audio_path is not None,
                duration=metadata.get('duration', 0),
                metadata=metadata
            )

        except Exception as e:
            # Cleanup on error
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

            return SeparationResult(
                success=False,
                video_path=None,
                audio_path=None,
                temp_dir=temp_dir,
                original_path=video_path,
                has_audio=False,
                duration=0,
                error=str(e),
                metadata=metadata
            )

    def _extract_audio(self, video_path: str, temp_dir: str) -> Optional[str]:
        """
        Extract audio track from video as 16kHz mono WAV.
        Format optimized for Whisper ASR.
        """
        # Generate secure filename
        audio_hash = hashlib.sha256(f"{video_path}_{secrets.token_hex(8)}".encode()).hexdigest()[:16]
        audio_path = os.path.join(temp_dir, "audio", f"audio_{audio_hash}.wav")

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",                    # No video
            "-acodec", "pcm_s16le",   # 16-bit PCM
            "-ar", "16000",           # 16kHz (Whisper optimal)
            "-ac", "1",               # Mono
            "-y",                     # Overwrite
            audio_path,
            "-loglevel", "error"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                print(f"ffmpeg audio extraction error: {result.stderr}")
                return None

            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                print(f"✓ Audio extracted: {os.path.basename(audio_path)}")
                return audio_path

            return None

        except subprocess.TimeoutExpired:
            print("⚠ Audio extraction timeout")
            return None
        except Exception as e:
            print(f"⚠ Audio extraction error: {e}")
            return None


# Convenience function
def separate_video_audio(video_path: str) -> SeparationResult:
    """Convenience function to separate video and audio."""
    separator = VideoAudioSeparator()
    return separator.separate(video_path)

