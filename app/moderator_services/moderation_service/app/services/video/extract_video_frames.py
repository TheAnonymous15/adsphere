"""
Video Frame Extractor - Extracts frames from video at configurable FPS
Second stage of video moderation pipeline

Input: Video file path + temp directory
Output: List of extracted frame paths
"""
import os
import subprocess
import secrets
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from app.core.config import settings


@dataclass
class FrameExtractionResult:
    """Result of frame extraction"""
    success: bool
    frame_paths: List[str]      # Paths to extracted frames
    frames_dir: str             # Directory containing frames
    frame_count: int            # Number of frames extracted
    fps_used: float             # Actual FPS used
    video_duration: float       # Video duration in seconds
    resolution: Tuple[int, int] # (width, height)
    error: Optional[str] = None


class VideoFrameExtractor:
    """
    Extracts frames from video files using ffmpeg.

    Features:
    - Configurable FPS (default: 2fps)
    - Maximum frame limit (default: 150)
    - Secure filename generation
    - Quality optimization
    - Resolution detection

    Receives video from: VideoAudioSeparator
    Sends frames to: VideoFrameProcessor
    """

    def __init__(
        self,
        fps: float = None,
        max_frames: int = None,
        output_format: str = "jpg",
        quality: int = 2  # ffmpeg quality (2=high, 31=low)
    ):
        """
        Initialize frame extractor.

        Args:
            fps: Frames per second to extract (default from config: 2.0)
            max_frames: Maximum frames to extract (default from config: 150)
            output_format: Output image format (jpg, png)
            quality: ffmpeg quality setting (2=high quality)
        """
        self.fps = fps or settings.FRAME_SAMPLE_FPS
        self.max_frames = max_frames or settings.MAX_FRAMES_PER_VIDEO
        self.output_format = output_format
        self.quality = quality

    def extract(
        self,
        video_path: str,
        output_dir: str,
        fps: float = None,
        max_frames: int = None
    ) -> FrameExtractionResult:
        """
        Extract frames from video.

        Args:
            video_path: Path to video file
            output_dir: Directory to save frames (usually temp_dir/frames)
            fps: Override default FPS
            max_frames: Override default max frames

        Returns:
            FrameExtractionResult with paths to extracted frames
        """
        fps = fps or self.fps
        max_frames = max_frames or self.max_frames

        # Validate video exists
        if not os.path.exists(video_path):
            return FrameExtractionResult(
                success=False,
                frame_paths=[],
                frames_dir=output_dir,
                frame_count=0,
                fps_used=fps,
                video_duration=0,
                resolution=(0, 0),
                error=f"Video file not found: {video_path}"
            )

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Get video metadata
        metadata = self._get_video_metadata(video_path)
        duration = metadata.get('duration', 0)
        width = metadata.get('width', 0)
        height = metadata.get('height', 0)

        if duration == 0:
            return FrameExtractionResult(
                success=False,
                frame_paths=[],
                frames_dir=output_dir,
                frame_count=0,
                fps_used=fps,
                video_duration=0,
                resolution=(width, height),
                error="Could not determine video duration"
            )

        # Calculate actual FPS to use (don't exceed max frames)
        total_frames_at_fps = int(duration * fps)
        actual_fps = fps

        if total_frames_at_fps > max_frames:
            actual_fps = max_frames / duration
            print(f"⚠ Adjusted FPS from {fps} to {actual_fps:.2f} to stay under {max_frames} frames")

        # Generate secure frame filename pattern
        secure_prefix = secrets.token_hex(8)
        frame_pattern = os.path.join(output_dir, f"frame_{secure_prefix}_%05d.{self.output_format}")

        # Extract frames using ffmpeg
        frame_paths = self._extract_with_ffmpeg(
            video_path,
            frame_pattern,
            actual_fps,
            max_frames
        )

        if not frame_paths:
            return FrameExtractionResult(
                success=False,
                frame_paths=[],
                frames_dir=output_dir,
                frame_count=0,
                fps_used=actual_fps,
                video_duration=duration,
                resolution=(width, height),
                error="Frame extraction failed - no frames produced"
            )

        print(f"✓ Extracted {len(frame_paths)} frames at {actual_fps:.2f} fps")

        return FrameExtractionResult(
            success=True,
            frame_paths=frame_paths,
            frames_dir=output_dir,
            frame_count=len(frame_paths),
            fps_used=actual_fps,
            video_duration=duration,
            resolution=(width, height)
        )

    def _extract_with_ffmpeg(
        self,
        video_path: str,
        frame_pattern: str,
        fps: float,
        max_frames: int
    ) -> List[str]:
        """
        Use ffmpeg to extract frames.

        Args:
            video_path: Source video
            frame_pattern: Output pattern (e.g., frame_%05d.jpg)
            fps: Frames per second
            max_frames: Maximum frames to extract

        Returns:
            List of paths to extracted frames
        """
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"fps={fps}",
            "-frames:v", str(max_frames),
            "-q:v", str(self.quality),
            frame_pattern,
            "-y",  # Overwrite
            "-loglevel", "error"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                print(f"ffmpeg error: {result.stderr}")
                return []

            # Collect extracted frames
            output_dir = os.path.dirname(frame_pattern)
            frame_files = sorted(Path(output_dir).glob(f"frame_*.{self.output_format}"))

            return [str(f) for f in frame_files]

        except subprocess.TimeoutExpired:
            print("⚠ Frame extraction timeout (5 min)")
            return []
        except Exception as e:
            print(f"⚠ Frame extraction error: {e}")
            return []

    def _get_video_metadata(self, video_path: str) -> Dict:
        """
        Get video metadata using ffprobe.
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
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            import json
            data = json.loads(result.stdout)

            video_stream = next(
                (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
                {}
            )

            format_info = data.get("format", {})

            return {
                "duration": float(format_info.get("duration", 0)),
                "width": int(video_stream.get("width", 0)),
                "height": int(video_stream.get("height", 0)),
            }
        except Exception as e:
            print(f"ffprobe error: {e}")
            return {"duration": 0, "width": 0, "height": 0}

    def extract_keyframes(self, video_path: str, output_dir: str) -> FrameExtractionResult:
        """
        Extract only keyframes (I-frames) from video.
        More efficient for quick analysis.

        Args:
            video_path: Source video
            output_dir: Output directory

        Returns:
            FrameExtractionResult
        """
        os.makedirs(output_dir, exist_ok=True)

        secure_prefix = secrets.token_hex(8)
        frame_pattern = os.path.join(output_dir, f"keyframe_{secure_prefix}_%05d.{self.output_format}")

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", "select='eq(pict_type,I)'",
            "-vsync", "vfr",
            "-frames:v", str(self.max_frames),
            "-q:v", str(self.quality),
            frame_pattern,
            "-y",
            "-loglevel", "error"
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            frame_files = sorted(Path(output_dir).glob(f"keyframe_*.{self.output_format}"))
            frame_paths = [str(f) for f in frame_files]

            metadata = self._get_video_metadata(video_path)

            return FrameExtractionResult(
                success=len(frame_paths) > 0,
                frame_paths=frame_paths,
                frames_dir=output_dir,
                frame_count=len(frame_paths),
                fps_used=0,  # N/A for keyframes
                video_duration=metadata.get('duration', 0),
                resolution=(metadata.get('width', 0), metadata.get('height', 0))
            )

        except Exception as e:
            return FrameExtractionResult(
                success=False,
                frame_paths=[],
                frames_dir=output_dir,
                frame_count=0,
                fps_used=0,
                video_duration=0,
                resolution=(0, 0),
                error=str(e)
            )

    def extract_thumbnails(
        self,
        video_path: str,
        output_dir: str,
        timestamps: List[float] = None,
        count: int = 5
    ) -> List[str]:
        """
        Extract thumbnails at specific timestamps or evenly distributed.

        Args:
            video_path: Source video
            output_dir: Output directory
            timestamps: Specific timestamps (seconds), or None for even distribution
            count: Number of thumbnails if timestamps not specified

        Returns:
            List of thumbnail paths
        """
        os.makedirs(output_dir, exist_ok=True)

        metadata = self._get_video_metadata(video_path)
        duration = metadata.get('duration', 0)

        if duration == 0:
            return []

        # Generate timestamps if not provided
        if timestamps is None:
            step = duration / (count + 1)
            timestamps = [step * (i + 1) for i in range(count)]

        thumbnails = []
        secure_prefix = secrets.token_hex(4)

        for i, ts in enumerate(timestamps):
            if ts > duration:
                continue

            output_path = os.path.join(output_dir, f"thumb_{secure_prefix}_{i:03d}.{self.output_format}")

            cmd = [
                "ffmpeg",
                "-ss", str(ts),
                "-i", video_path,
                "-frames:v", "1",
                "-q:v", str(self.quality),
                output_path,
                "-y",
                "-loglevel", "error"
            ]

            try:
                subprocess.run(cmd, capture_output=True, timeout=30)
                if os.path.exists(output_path):
                    thumbnails.append(output_path)
            except:
                pass

        return thumbnails


# Convenience function
def extract_frames(
    video_path: str,
    output_dir: str,
    fps: float = 2.0,
    max_frames: int = 150
) -> FrameExtractionResult:
    """
    Convenience function to extract video frames.

    Usage:
        result = extract_frames("/path/to/video.mp4", "/tmp/frames")
        for frame in result.frame_paths:
            # Process each frame
    """
    extractor = VideoFrameExtractor(fps=fps, max_frames=max_frames)
    return extractor.extract(video_path, output_dir)

