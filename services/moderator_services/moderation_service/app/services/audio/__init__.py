"""
Audio Processing Module
Contains audio moderation components

Components:
1. audio_processor.py - Single audio file processing
2. audio_chunk_processor.py - Parallel chunk processing (10 chunks for 60s audio)
"""

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

