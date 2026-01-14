"""
YouTube Video Processor - Downloads and processes YouTube videos for moderation
Supports: YouTube URLs, YouTube Shorts, and other yt-dlp supported platforms

Features:
1. Download video from YouTube URL
2. Extract audio and video streams
3. Process through moderation pipeline
4. Support for age-restricted content (with cookies)
5. Automatic cleanup of downloaded files
"""
import os
import asyncio
import subprocess
import tempfile
import secrets
import re
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class YouTubeVideoInfo:
    """Information about a YouTube video"""
    url: str
    video_id: str
    title: str = ""
    duration: float = 0.0  # seconds
    channel: str = ""
    description: str = ""
    upload_date: str = ""
    view_count: int = 0
    like_count: int = 0
    is_live: bool = False
    is_age_restricted: bool = False
    thumbnail_url: str = ""
    formats_available: list = field(default_factory=list)


@dataclass
class YouTubeDownloadResult:
    """Result of downloading a YouTube video"""
    success: bool
    video_path: Optional[str] = None
    audio_path: Optional[str] = None
    temp_dir: str = ""
    video_info: Optional[YouTubeVideoInfo] = None
    error: Optional[str] = None
    download_time_ms: float = 0.0


class YouTubeProcessor:
    """
    Downloads and processes YouTube videos for content moderation.

    Uses yt-dlp (youtube-dl fork) for downloading.

    Usage:
        processor = YouTubeProcessor()

        # Get video info first
        info = await processor.get_video_info("https://youtube.com/watch?v=xxx")

        # Download and process
        result = await processor.download_video("https://youtube.com/watch?v=xxx")

        # Then run through moderation pipeline
        from app.services.video_moderation_pipeline import VideoModerationPipeline
        pipeline = VideoModerationPipeline()
        moderation_result = await pipeline.moderate_video_async(result.video_path)
    """

    # Maximum video duration to process (in seconds)
    MAX_DURATION_SECONDS = 300  # 5 minutes max

    # Supported URL patterns
    YOUTUBE_PATTERNS = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})',
    ]

    def __init__(
        self,
        max_duration: int = None,
        prefer_quality: str = "720",
        download_audio_only: bool = False
    ):
        """
        Initialize YouTube processor.

        Args:
            max_duration: Maximum video duration in seconds (default: 300)
            prefer_quality: Preferred video quality (360, 480, 720, 1080)
            download_audio_only: Only download audio track
        """
        self.max_duration = max_duration or self.MAX_DURATION_SECONDS
        self.prefer_quality = prefer_quality
        self.download_audio_only = download_audio_only

        # Check if yt-dlp is available
        self._check_ytdlp()

    def _check_ytdlp(self):
        """Check if yt-dlp is installed."""
        try:
            result = subprocess.run(
                ["yt-dlp", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"✓ yt-dlp version: {result.stdout.strip()}")
            else:
                print("⚠ yt-dlp not found. Install with: pip install yt-dlp")
        except FileNotFoundError:
            print("⚠ yt-dlp not found. Install with: pip install yt-dlp")
        except Exception as e:
            print(f"⚠ Error checking yt-dlp: {e}")

    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        for pattern in self.YOUTUBE_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def is_valid_youtube_url(self, url: str) -> bool:
        """Check if URL is a valid YouTube URL."""
        return self.extract_video_id(url) is not None

    async def get_video_info(self, url: str) -> Optional[YouTubeVideoInfo]:
        """
        Get video information without downloading.

        Args:
            url: YouTube video URL

        Returns:
            YouTubeVideoInfo or None if failed
        """
        video_id = self.extract_video_id(url)
        if not video_id:
            return None

        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-download",
            "--no-playlist",
            url
        ]

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                result.communicate(),
                timeout=30
            )

            if result.returncode != 0:
                print(f"⚠ Failed to get video info: {stderr.decode()}")
                return None

            import json
            info = json.loads(stdout.decode())

            return YouTubeVideoInfo(
                url=url,
                video_id=video_id,
                title=info.get('title', ''),
                duration=float(info.get('duration', 0)),
                channel=info.get('channel', info.get('uploader', '')),
                description=info.get('description', ''),
                upload_date=info.get('upload_date', ''),
                view_count=int(info.get('view_count', 0)),
                like_count=int(info.get('like_count', 0)),
                is_live=info.get('is_live', False),
                is_age_restricted=info.get('age_limit', 0) >= 18,
                thumbnail_url=info.get('thumbnail', ''),
                formats_available=[f.get('format_note', '') for f in info.get('formats', [])]
            )

        except asyncio.TimeoutError:
            print("⚠ Timeout getting video info")
            return None
        except Exception as e:
            print(f"⚠ Error getting video info: {e}")
            return None

    async def download_video(
        self,
        url: str,
        output_dir: str = None
    ) -> YouTubeDownloadResult:
        """
        Download YouTube video for processing.

        Args:
            url: YouTube video URL
            output_dir: Directory to save video (temp if None)

        Returns:
            YouTubeDownloadResult with paths to downloaded files
        """
        import time
        start_time = time.time()

        # Validate URL
        video_id = self.extract_video_id(url)
        if not video_id:
            return YouTubeDownloadResult(
                success=False,
                error=f"Invalid YouTube URL: {url}"
            )

        # Get video info first
        video_info = await self.get_video_info(url)

        if video_info:
            # Check duration limit
            if video_info.duration > self.max_duration:
                return YouTubeDownloadResult(
                    success=False,
                    video_info=video_info,
                    error=f"Video too long: {video_info.duration:.0f}s > {self.max_duration}s max"
                )

            # Check if live stream
            if video_info.is_live:
                return YouTubeDownloadResult(
                    success=False,
                    video_info=video_info,
                    error="Cannot process live streams"
                )

            print(f"📺 Downloading: {video_info.title}")
            print(f"   Duration: {video_info.duration:.0f}s, Channel: {video_info.channel}")

        # Create temp directory
        if output_dir is None:
            secure_name = f"yt_{secrets.token_hex(16)}"
            output_dir = os.path.join(tempfile.gettempdir(), secure_name)

        os.makedirs(output_dir, exist_ok=True)

        try:
            # Download video
            video_path = await self._download_video_file(url, output_dir, video_id)

            if not video_path:
                return YouTubeDownloadResult(
                    success=False,
                    temp_dir=output_dir,
                    video_info=video_info,
                    error="Failed to download video"
                )

            # Extract audio separately (for parallel processing)
            audio_path = await self._extract_audio(video_path, output_dir)

            download_time = (time.time() - start_time) * 1000

            print(f"✅ Downloaded in {download_time:.0f}ms")
            print(f"   Video: {os.path.basename(video_path)}")
            if audio_path:
                print(f"   Audio: {os.path.basename(audio_path)}")

            return YouTubeDownloadResult(
                success=True,
                video_path=video_path,
                audio_path=audio_path,
                temp_dir=output_dir,
                video_info=video_info,
                download_time_ms=download_time
            )

        except Exception as e:
            return YouTubeDownloadResult(
                success=False,
                temp_dir=output_dir,
                video_info=video_info,
                error=str(e)
            )

    async def _download_video_file(
        self,
        url: str,
        output_dir: str,
        video_id: str
    ) -> Optional[str]:
        """Download video file using yt-dlp."""

        output_template = os.path.join(output_dir, f"{video_id}.%(ext)s")

        # Build yt-dlp command
        cmd = [
            "yt-dlp",
            "-f", f"bestvideo[height<={self.prefer_quality}]+bestaudio/best[height<={self.prefer_quality}]",
            "--merge-output-format", "mp4",
            "-o", output_template,
            "--no-playlist",
            "--no-warnings",
            "--quiet",
            url
        ]

        if self.download_audio_only:
            cmd = [
                "yt-dlp",
                "-f", "bestaudio",
                "-x", "--audio-format", "wav",
                "-o", output_template,
                "--no-playlist",
                "--no-warnings",
                "--quiet",
                url
            ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait with timeout (5 minutes for large videos)
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300
            )

            if process.returncode != 0:
                print(f"⚠ yt-dlp error: {stderr.decode()}")
                return None

            # Find downloaded file
            for ext in ['mp4', 'webm', 'mkv', 'wav', 'mp3']:
                video_path = os.path.join(output_dir, f"{video_id}.{ext}")
                if os.path.exists(video_path):
                    return video_path

            # Check for any video file
            for f in os.listdir(output_dir):
                if f.startswith(video_id):
                    return os.path.join(output_dir, f)

            return None

        except asyncio.TimeoutError:
            print("⚠ Download timeout (5 min)")
            return None
        except Exception as e:
            print(f"⚠ Download error: {e}")
            return None

    async def _extract_audio(self, video_path: str, output_dir: str) -> Optional[str]:
        """Extract audio from video for parallel processing."""

        audio_filename = f"audio_{secrets.token_hex(8)}.wav"
        audio_path = os.path.join(output_dir, audio_filename)

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            "-y",
            audio_path,
            "-loglevel", "error"
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            await asyncio.wait_for(process.communicate(), timeout=120)

            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                return audio_path

            return None

        except Exception as e:
            print(f"⚠ Audio extraction error: {e}")
            return None

    def cleanup(self, download_result: YouTubeDownloadResult):
        """Clean up downloaded files."""
        import shutil

        if download_result.temp_dir and os.path.exists(download_result.temp_dir):
            try:
                shutil.rmtree(download_result.temp_dir)
                print(f"✓ Cleaned up: {os.path.basename(download_result.temp_dir)}")
            except Exception as e:
                print(f"⚠ Cleanup error: {e}")


async def moderate_youtube_video(
    url: str,
    max_duration: int = 300,
    batch_size: int = 8,
    audio_chunks: int = 10
) -> Dict:
    """
    Complete pipeline: Download YouTube video and run moderation.

    Args:
        url: YouTube video URL
        max_duration: Maximum video duration in seconds
        batch_size: Batch size for frame processing
        audio_chunks: Number of audio chunks for parallel processing

    Returns:
        Moderation result dictionary

    Usage:
        result = await moderate_youtube_video("https://youtube.com/watch?v=xxx")
        print(f"Decision: {result['decision']}")
    """
    from app.services.video_moderation_pipeline import VideoModerationPipeline

    processor = YouTubeProcessor(max_duration=max_duration)
    pipeline = VideoModerationPipeline(
        batch_size=batch_size,
        audio_chunks=audio_chunks
    )

    # Step 1: Download video
    print(f"🔗 Processing YouTube URL: {url}")
    download_result = await processor.download_video(url)

    if not download_result.success:
        return {
            "success": False,
            "error": download_result.error,
            "video_info": download_result.video_info.__dict__ if download_result.video_info else None
        }

    try:
        # Step 2: Run moderation pipeline
        print(f"🔍 Running moderation pipeline...")
        moderation_result = await pipeline.moderate_video_async(download_result.video_path)

        # Step 3: Combine results
        return {
            "success": True,
            "youtube_info": {
                "video_id": download_result.video_info.video_id if download_result.video_info else None,
                "title": download_result.video_info.title if download_result.video_info else None,
                "channel": download_result.video_info.channel if download_result.video_info else None,
                "duration": download_result.video_info.duration if download_result.video_info else None,
                "url": url
            },
            "moderation": {
                "decision": moderation_result.decision,
                "risk_level": moderation_result.risk_level,
                "global_score": moderation_result.global_score,
                "category_scores": moderation_result.category_scores,
                "flags": moderation_result.flags,
                "reasons": moderation_result.reasons,
                "frames_analyzed": moderation_result.frames_analyzed,
                "processing_time_ms": moderation_result.processing_time_ms
            },
            "download_time_ms": download_result.download_time_ms
        }

    finally:
        # Step 4: Cleanup
        processor.cleanup(download_result)


# Convenience function for quick checks
async def check_youtube_video(url: str) -> Dict:
    """
    Quick check of YouTube video without full moderation.
    Just gets video info and checks basic metadata.

    Args:
        url: YouTube video URL

    Returns:
        Video info and basic checks
    """
    processor = YouTubeProcessor()

    info = await processor.get_video_info(url)

    if not info:
        return {
            "valid": False,
            "error": "Could not fetch video info"
        }

    # Basic checks
    warnings = []

    if info.duration > 300:
        warnings.append(f"Video is long ({info.duration:.0f}s)")

    if info.is_live:
        warnings.append("This is a live stream")

    if info.is_age_restricted:
        warnings.append("Age-restricted content")

    # Check title/description for obvious issues
    text_to_check = f"{info.title} {info.description}".lower()
    suspicious_words = ['nsfw', 'xxx', 'porn', 'nude', 'violence', 'gore', 'kill']

    for word in suspicious_words:
        if word in text_to_check:
            warnings.append(f"Suspicious keyword in metadata: {word}")

    return {
        "valid": True,
        "video_id": info.video_id,
        "title": info.title,
        "channel": info.channel,
        "duration": info.duration,
        "view_count": info.view_count,
        "is_live": info.is_live,
        "is_age_restricted": info.is_age_restricted,
        "warnings": warnings,
        "can_process": len(warnings) == 0 or not info.is_live
    }

