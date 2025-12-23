"""
Video Processing Module
Contains all video moderation components

Pipeline Flow:
1. separate_video_audio.py - Entry point, splits video and audio
2. extract_video_frames.py - Extracts frames at 2fps
3. video_frame_processor.py - Analyzes frames (NSFW, violence, etc.)
4. async_frame_processor.py - Async parallel frame analysis (120 workers)
5. youtube_processor.py - Download and process YouTube videos
"""

import sys
from pathlib import Path

# Set up paths for model_registry import
# Path: video/__init__.py -> video -> services -> app -> moderation_service -> moderator_services
VIDEO_DIR = Path(__file__).parent.resolve()
SERVICES_DIR = VIDEO_DIR.parent.resolve()
APP_DIR = SERVICES_DIR.parent.resolve()
MODERATION_SERVICE_DIR = APP_DIR.parent.resolve()
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent.resolve()

for _path in [str(MODERATOR_SERVICES_DIR), str(MODERATION_SERVICE_DIR), str(APP_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from app.services.video.separate_video_audio import (
    VideoAudioSeparator,
    SeparationResult,
    separate_video_audio
)

from app.services.video.extract_video_frames import (
    VideoFrameExtractor,
    FrameExtractionResult,
    extract_frames
)

from app.services.video.video_frame_processor import (
    VideoFrameProcessor,
    VideoFrameProcessorResult,
    FrameAnalysis,
    process_video_frames
)

from app.services.video.async_frame_processor import (
    AsyncVideoFrameProcessor,
    AsyncFrameProcessorResult,
    process_frames_async
)

from app.services.video.youtube_processor import (
    YouTubeProcessor,
    YouTubeVideoInfo,
    YouTubeDownloadResult,
    moderate_youtube_video,
    check_youtube_video
)

__all__ = [
    # Separator
    'VideoAudioSeparator',
    'SeparationResult',
    'separate_video_audio',

    # Frame Extractor
    'VideoFrameExtractor',
    'FrameExtractionResult',
    'extract_frames',

    # Frame Processor (Sync)
    'VideoFrameProcessor',
    'VideoFrameProcessorResult',
    'FrameAnalysis',
    'process_video_frames',

    # Async Frame Processor
    'AsyncVideoFrameProcessor',
    'AsyncFrameProcessorResult',
    'process_frames_async',

    # YouTube Processor
    'YouTubeProcessor',
    'YouTubeVideoInfo',
    'YouTubeDownloadResult',
    'moderate_youtube_video',
    'check_youtube_video'
]

