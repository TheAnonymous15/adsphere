"""
Audio Processing Module
Contains audio moderation components

Components:
1. audio_processor.py - Single audio file processing
2. audio_chunk_processor.py - Parallel chunk processing (10 chunks for 60s audio)
"""

import sys
from pathlib import Path

# Set up paths for model_registry import
# Path: audio/__init__.py -> audio -> services -> app -> moderation_service -> moderator_services
AUDIO_DIR = Path(__file__).parent.resolve()
SERVICES_DIR = AUDIO_DIR.parent.resolve()
APP_DIR = SERVICES_DIR.parent.resolve()
MODERATION_SERVICE_DIR = APP_DIR.parent.resolve()
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent.resolve()

for _path in [str(MODERATOR_SERVICES_DIR), str(MODERATION_SERVICE_DIR), str(APP_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from app.services.audio.audio_processor import (
    AudioProcessor,
    AudioModerationResult,
    process_audio
)

from app.services.audio.audio_chunk_processor import (
    AudioChunker,
    AudioChunk,
    ChunkAnalysisResult,
    AudioAnalysisResult,
    AsyncAudioChunkProcessor,
    analyze_audio_parallel
)

__all__ = [
    # Single file processor
    'AudioProcessor',
    'AudioModerationResult',
    'process_audio',

    # Chunk-based parallel processor
    'AudioChunker',
    'AudioChunk',
    'ChunkAnalysisResult',
    'AudioAnalysisResult',
    'AsyncAudioChunkProcessor',
    'analyze_audio_parallel'
]

