"""
Complete Video Moderation Pipeline - REDESIGNED
Orchestrates all video analysis services using modular components

Pipeline Flow:
    Video File
        │
        ▼
    ┌─────────────────────────────────┐
    │ 1. VideoAudioSeparator          │
    │    - Validate video             │
    │    - Create secure temp dir     │
    │    - Extract audio track        │
    └─────────────────────────────────┘
        │                    │
        │                    ▼
        │         ┌─────────────────────────┐
        │         │ 2a. AudioProcessor      │
        │         │     - ASR (Whisper)     │
        │         │     - Toxicity analysis │
        │         └─────────────────────────┘
        │                    │
        ▼                    │
    ┌─────────────────────────────────┐
    │ 2b. VideoFrameExtractor         │
    │     - Extract frames at 2fps    │
    │     - Max 150 frames           │
    └─────────────────────────────────┘
        │
        ▼
    ┌─────────────────────────────────┐
    │ 3. VideoFrameProcessor          │
    │    - NSFW detection             │
    │    - Violence detection         │
    │    - Weapon detection           │
    │    - Blood detection            │
    │    - OCR text extraction        │
    │    - Object detection           │
    └─────────────────────────────────┘
        │
        ▼
    ┌─────────────────────────────────┐
    │ 4. Decision Engine              │
    │    - Aggregate all scores       │
    │    - Apply thresholds           │
    │    - Return: approve/review/block│
    └─────────────────────────────────┘
        │
        ▼
    Cleanup temp directory
"""
import os
import sys
import shutil
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

# Set up paths for model_registry import
# Path: services/video_moderation_pipeline.py -> services -> app -> moderation_service -> moderator_services
CURRENT_DIR = Path(__file__).parent.resolve()
APP_DIR = CURRENT_DIR.parent.resolve()
MODERATION_SERVICE_DIR = APP_DIR.parent.resolve()
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent.resolve()

for _path in [str(MODERATOR_SERVICES_DIR), str(MODERATION_SERVICE_DIR), str(APP_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from model_registry import ensure_models

# Ensure core models are available
REQUIRED_MODELS = ['yolov8n', 'whisper', 'detoxify', 'paddleocr', 'ultralytics', 'torch']
if not ensure_models(REQUIRED_MODELS, verbose=False):
    print("⚠ VideoModerationPipeline: Some models not available, continuing with available models...")

# Import new modular components
from app.services.video.separate_video_audio import VideoAudioSeparator, SeparationResult
from app.services.video.extract_video_frames import VideoFrameExtractor, FrameExtractionResult
from app.services.video.video_frame_processor import VideoFrameProcessor, VideoFrameProcessorResult
from app.services.audio.audio_processor import AudioProcessor, AudioModerationResult

# Parallel audio chunk processor (10 chunks for 60s audio)
from app.services.audio.audio_chunk_processor import AsyncAudioChunkProcessor, AudioAnalysisResult

# Async processor using BatchCoordinator for parallel frame analysis
from app.services.video.async_frame_processor import AsyncVideoFrameProcessor, AsyncFrameProcessorResult

# Import decision engine and schemas
from app.core.decision_engine import DecisionEngine
from app.models.schemas import CategoryScores
from app.core.config import settings


@dataclass
class VideoModerationResult:
    """Complete video moderation result"""
    success: bool
    decision: str  # approve, review, block
    risk_level: str  # low, medium, high, critical
    global_score: float  # 0.0 - 1.0 (1.0 = safe)

    # Category scores
    category_scores: Dict[str, float] = field(default_factory=dict)

    # Flags and reasons
    flags: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)

    # Processing details
    frames_analyzed: int = 0
    has_audio: bool = False
    audio_transcription: str = ""
    ocr_text: str = ""

    # AI sources
    ai_sources: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    video_duration: float = 0.0
    fps_used: float = 0.0
    processing_time_ms: float = 0.0

    # Error
    error: Optional[str] = None


# Need to import List for type hints
from typing import List


class VideoModerationPipeline:
    """
    Complete video moderation pipeline using modular components.

    This is the MAIN ENTRY POINT for video moderation.

    Usage:
        pipeline = VideoModerationPipeline()
        result = pipeline.moderate_video("/path/to/video.mp4")

        if result.decision == 'block':
            # Reject video
        elif result.decision == 'review':
            # Flag for manual review
        else:
            # Approve video
    """

    def __init__(
        self,
        fps: float = None,
        max_frames: int = None,
        whisper_model: str = "small",
        parallel_frames: bool = True,
        use_batch_coordinator: bool = True,
        batch_size: int = 8,
        audio_chunks: int = 10
    ):
        """
        Initialize video moderation pipeline.

        Args:
            fps: Frames per second to extract (default: from config)
            max_frames: Maximum frames to extract (default: from config)
            whisper_model: Whisper model size for ASR
            parallel_frames: Process frames in parallel (sync mode)
            use_batch_coordinator: Use BatchCoordinator for async processing
            batch_size: Batch size for BatchCoordinator (default: 8 frames per batch)
            audio_chunks: Number of audio chunks for parallel processing (default: 10)
        """
        self.fps = fps or settings.FRAME_SAMPLE_FPS
        self.max_frames = max_frames or settings.MAX_FRAMES_PER_VIDEO
        self.use_batch_coordinator = use_batch_coordinator
        self.batch_size = batch_size
        self.audio_chunks = audio_chunks

        # Initialize components
        self.separator = VideoAudioSeparator()
        self.frame_extractor = VideoFrameExtractor(fps=self.fps, max_frames=self.max_frames)

        # Frame processors (sync and async)
        self.frame_processor = VideoFrameProcessor(parallel=parallel_frames)
        if use_batch_coordinator:
            self.async_frame_processor = AsyncVideoFrameProcessor(batch_size=batch_size)

        # Audio processors (sync and async)
        self.audio_processor = AudioProcessor(whisper_model=whisper_model)
        self.async_audio_processor = AsyncAudioChunkProcessor(num_chunks=audio_chunks)

        # Text moderation for combined OCR + ASR text
        self.text_moderator = None
        try:
            from app.services.text_detoxify import DetoxifyService
            self.text_moderator = DetoxifyService()
        except Exception as e:
            print(f"⚠ Text moderator not available: {e}")

    def moderate_video(self, video_path: str) -> VideoModerationResult:
        """
        Run complete moderation pipeline on video.

        Args:
            video_path: Path to video file

        Returns:
            VideoModerationResult with decision and details
        """
        start_time = time.time()
        temp_dir = None

        try:
            # ========================================
            # STEP 1: Separate Video and Audio
            # ========================================
            print(f"[1/4] Separating video and audio...")
            separation_result = self.separator.separate(video_path)

            if not separation_result.success:
                return VideoModerationResult(
                    success=False,
                    decision="block",
                    risk_level="critical",
                    global_score=0.0,
                    error=separation_result.error
                )

            temp_dir = separation_result.temp_dir

            # ========================================
            # STEP 2a: Process Audio (if available)
            # ========================================
            audio_result = None
            audio_text = ""

            if separation_result.has_audio and separation_result.audio_path:
                print(f"[2a/4] Processing audio...")
                audio_result = self.audio_processor.process(separation_result.audio_path)

                if audio_result.success:
                    audio_text = audio_result.transcription
                    print(f"  ✓ Transcribed {len(audio_text)} characters, language: {audio_result.language}")
            else:
                print(f"[2a/4] No audio track found, skipping...")

            # ========================================
            # STEP 2b: Extract Video Frames
            # ========================================
            print(f"[2b/4] Extracting frames at {self.fps} fps...")
            frames_dir = os.path.join(temp_dir, "frames")

            extraction_result = self.frame_extractor.extract(
                separation_result.video_path,
                frames_dir,
                fps=self.fps,
                max_frames=self.max_frames
            )

            if not extraction_result.success:
                return VideoModerationResult(
                    success=False,
                    decision="review",
                    risk_level="medium",
                    global_score=0.5,
                    error=extraction_result.error,
                    video_duration=separation_result.duration
                )

            print(f"  ✓ Extracted {extraction_result.frame_count} frames")

            # ========================================
            # STEP 3: Process Frames
            # ========================================
            print(f"[3/4] Analyzing {extraction_result.frame_count} frames...")

            frame_result = self.frame_processor.process_frames(
                extraction_result.frame_paths,
                fps_used=extraction_result.fps_used
            )

            if not frame_result.success:
                return VideoModerationResult(
                    success=False,
                    decision="review",
                    risk_level="medium",
                    global_score=0.5,
                    error=frame_result.error,
                    video_duration=separation_result.duration,
                    frames_analyzed=extraction_result.frame_count
                )

            print(f"  ✓ Analyzed frames, found {len(frame_result.all_flags)} flags")

            # ========================================
            # STEP 4: Aggregate and Decide
            # ========================================
            print(f"[4/4] Making decision...")

            # Combine all text (OCR from frames + ASR from audio)
            combined_text = ""
            if frame_result.all_text:
                combined_text += f"[Video Text]\n{frame_result.all_text}\n\n"
            if audio_text:
                combined_text += f"[Audio Transcription]\n{audio_text}"

            # Analyze combined text if present
            text_toxicity_scores = {}
            if combined_text.strip() and self.text_moderator:
                try:
                    text_toxicity_scores = self.text_moderator.analyze(combined_text)
                except Exception as e:
                    print(f"  ⚠ Text moderation failed: {e}")

            # Build final category scores
            category_scores = frame_result.category_scores.copy()

            # Merge text toxicity into category scores
            if text_toxicity_scores:
                category_scores['hate'] = max(
                    category_scores.get('hate', 0.0),
                    text_toxicity_scores.get('toxicity', 0.0)
                )
                category_scores['self_harm'] = max(
                    category_scores.get('self_harm', 0.0),
                    text_toxicity_scores.get('identity_attack', 0.0) * 0.5
                )

            # Merge audio toxicity if available
            if audio_result and audio_result.success:
                for key, value in audio_result.toxicity_scores.items():
                    if key not in ['error']:
                        if key == 'toxicity':
                            category_scores['hate'] = max(category_scores.get('hate', 0.0), value)
                        elif key == 'threat':
                            category_scores['violence'] = max(category_scores.get('violence', 0.0), value)

            # Make decision
            decision, risk_level, flags, reasons = DecisionEngine.decide(category_scores)
            global_score = DecisionEngine.calculate_global_score(category_scores)

            # Combine all flags
            all_flags = list(set(flags + frame_result.all_flags))
            if audio_result and audio_result.flags:
                all_flags.extend(audio_result.flags)
            all_flags = list(set(all_flags))

            # Build AI sources
            ai_sources = frame_result.ai_sources.copy()
            if audio_result:
                ai_sources['audio'] = {
                    'transcription_length': len(audio_text),
                    'language': audio_result.language,
                    'risk_level': audio_result.risk_level,
                    'flags': audio_result.flags
                }
            if text_toxicity_scores:
                ai_sources['text_toxicity'] = text_toxicity_scores

            processing_time = (time.time() - start_time) * 1000

            print(f"  ✓ Decision: {decision.upper()}, Risk: {risk_level}")
            print(f"  ✓ Total processing time: {processing_time:.0f}ms")

            return VideoModerationResult(
                success=True,
                decision=decision,
                risk_level=risk_level,
                global_score=global_score,
                category_scores=category_scores,
                flags=all_flags,
                reasons=reasons,
                frames_analyzed=frame_result.frames_analyzed,
                has_audio=separation_result.has_audio,
                audio_transcription=audio_text,
                ocr_text=frame_result.all_text,
                ai_sources=ai_sources,
                video_duration=separation_result.duration,
                fps_used=extraction_result.fps_used,
                processing_time_ms=processing_time
            )

        except Exception as e:
            import traceback
            error_msg = f"Video moderation failed: {str(e)}"
            print(f"  ❌ {error_msg}")
            traceback.print_exc()

            return VideoModerationResult(
                success=False,
                decision="review",
                risk_level="high",
                global_score=0.5,
                error=error_msg
            )

        finally:
            # GUARANTEED CLEANUP: Delete temp directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    print(f"  ✓ Cleaned up: {os.path.basename(temp_dir)}")
                except Exception as e:
                    print(f"  ⚠ Cleanup failed: {e}")

    async def moderate_video_async(self, video_path: str) -> VideoModerationResult:
        """
        Run complete moderation pipeline on video using async workers.

        This version uses 120 async workers for parallel frame processing.
        Much faster for videos with many frames (60s video = 120 frames).

        Args:
            video_path: Path to video file

        Returns:
            VideoModerationResult with decision and details
        """
        start_time = time.time()
        temp_dir = None

        try:
            # STEP 1: Separate Video and Audio
            print(f"[1/4] Separating video and audio...")
            separation_result = self.separator.separate(video_path)

            if not separation_result.success:
                return VideoModerationResult(
                    success=False,
                    decision="block",
                    risk_level="critical",
                    global_score=0.0,
                    error=separation_result.error
                )

            temp_dir = separation_result.temp_dir

            # STEP 2a: Process Audio in PARALLEL CHUNKS
            audio_result = None
            audio_text = ""
            audio_flags = []

            if separation_result.has_audio and separation_result.audio_path:
                print(f"[2a/4] Processing audio in {self.audio_chunks} parallel chunks...")

                # Use parallel audio chunk processor
                audio_result = await self.async_audio_processor.process_audio_async(
                    separation_result.audio_path,
                    temp_dir=os.path.join(temp_dir, "audio_chunks")
                )

                if audio_result.success:
                    audio_text = audio_result.full_transcription
                    audio_flags = audio_result.all_flags
                    print(f"  ✓ Transcribed {len(audio_text)} chars in {audio_result.chunks_processed} chunks")
                    print(f"    Language: {audio_result.detected_language}, Risk: {audio_result.risk_level}")
                    if audio_result.flagged_segments:
                        print(f"    ⚠ {len(audio_result.flagged_segments)} flagged segments found")
            else:
                print(f"[2a/4] No audio track found, skipping...")

            # STEP 2b: Extract Video Frames
            print(f"[2b/4] Extracting frames at {self.fps} fps...")
            frames_dir = os.path.join(temp_dir, "frames")

            extraction_result = self.frame_extractor.extract(
                separation_result.video_path,
                frames_dir,
                fps=self.fps,
                max_frames=self.max_frames
            )

            if not extraction_result.success:
                return VideoModerationResult(
                    success=False,
                    decision="review",
                    risk_level="medium",
                    global_score=0.5,
                    error=extraction_result.error,
                    video_duration=separation_result.duration
                )

            print(f"  ✓ Extracted {extraction_result.frame_count} frames")

            # STEP 3: Process Frames with ASYNC WORKERS
            print(f"[3/4] Analyzing {extraction_result.frame_count} frames with {self.max_async_workers} async workers...")

            # Use async processor for parallel frame analysis
            frame_result = await self.async_frame_processor.process_frames_async(
                extraction_result.frame_paths,
                fps_used=extraction_result.fps_used
            )

            if not frame_result.success:
                return VideoModerationResult(
                    success=False,
                    decision="review",
                    risk_level="medium",
                    global_score=0.5,
                    error=frame_result.error,
                    video_duration=separation_result.duration,
                    frames_analyzed=extraction_result.frame_count
                )

            print(f"  ✓ Analyzed frames in {frame_result.total_processing_time_ms:.0f}ms, found {len(frame_result.all_flags)} flags")

            # STEP 4: Aggregate and Decide
            print(f"[4/4] Making decision...")

            # Combine all text (OCR from frames + ASR from audio)
            combined_text = ""
            if frame_result.all_text:
                combined_text += f"[Video Text]\n{frame_result.all_text}\n\n"
            if audio_text:
                combined_text += f"[Audio Transcription]\n{audio_text}"

            # Analyze combined text if present
            text_toxicity_scores = {}
            if combined_text.strip() and self.text_moderator:
                try:
                    text_toxicity_scores = self.text_moderator.analyze(combined_text)
                except Exception as e:
                    print(f"  ⚠ Text moderation failed: {e}")

            # Build final category scores
            category_scores = frame_result.category_scores.copy()

            # Merge text toxicity into category scores
            if text_toxicity_scores:
                category_scores['hate'] = max(
                    category_scores.get('hate', 0.0),
                    text_toxicity_scores.get('toxicity', 0.0)
                )

            # Merge audio toxicity from parallel chunk analysis
            if audio_result and audio_result.success:
                for key, value in audio_result.max_toxicity_scores.items():
                    if key == 'toxicity':
                        category_scores['hate'] = max(category_scores.get('hate', 0.0), value)
                    elif key == 'threat':
                        category_scores['violence'] = max(category_scores.get('violence', 0.0), value)
                    elif key == 'severe_toxicity':
                        category_scores['hate'] = max(category_scores.get('hate', 0.0), value)

            # Make decision
            decision, risk_level, flags, reasons = DecisionEngine.decide(category_scores)
            global_score = DecisionEngine.calculate_global_score(category_scores)

            # Combine all flags (video + audio)
            all_flags = list(set(flags + frame_result.all_flags))
            if audio_flags:
                all_flags.extend(audio_flags)
            all_flags = list(set(all_flags))

            # Build AI sources
            ai_sources = frame_result.ai_sources.copy()
            ai_sources['batch_size'] = self.batch_size
            ai_sources['batches_processed'] = frame_result.batches_processed

            if audio_result and audio_result.success:
                ai_sources['audio'] = {
                    'transcription_length': len(audio_text),
                    'language': audio_result.detected_language,
                    'risk_level': audio_result.risk_level,
                    'chunks_processed': audio_result.chunks_processed,
                    'parallel_workers': audio_result.parallel_workers,
                    'avg_chunk_time_ms': audio_result.avg_chunk_time_ms,
                    'flagged_segments': len(audio_result.flagged_segments),
                    'flags': audio_flags
                }
            if text_toxicity_scores:
                ai_sources['text_toxicity'] = text_toxicity_scores

            processing_time = (time.time() - start_time) * 1000

            print(f"  ✓ Decision: {decision.upper()}, Risk: {risk_level}")
            print(f"  ✓ Total processing time: {processing_time:.0f}ms")

            return VideoModerationResult(
                success=True,
                decision=decision,
                risk_level=risk_level,
                global_score=global_score,
                category_scores=category_scores,
                flags=all_flags,
                reasons=reasons,
                frames_analyzed=frame_result.frames_analyzed,
                has_audio=separation_result.has_audio,
                audio_transcription=audio_text,
                ocr_text=frame_result.all_text,
                ai_sources=ai_sources,
                video_duration=separation_result.duration,
                fps_used=extraction_result.fps_used,
                processing_time_ms=processing_time
            )

        except Exception as e:
            import traceback
            error_msg = f"Async video moderation failed: {str(e)}"
            print(f"  ❌ {error_msg}")
            traceback.print_exc()

            return VideoModerationResult(
                success=False,
                decision="review",
                risk_level="high",
                global_score=0.5,
                error=error_msg
            )

        finally:
            # GUARANTEED CLEANUP
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    print(f"  ✓ Cleaned up: {os.path.basename(temp_dir)}")
                except Exception as e:
                    print(f"  ⚠ Cleanup failed: {e}")


# Convenience function (sync)
def moderate_video(video_path: str) -> VideoModerationResult:
    """
    Convenience function to moderate a video (sync).

    Usage:
        result = moderate_video("/path/to/video.mp4")
        print(f"Decision: {result.decision}")
    """
    pipeline = VideoModerationPipeline(use_async=False)
    return pipeline.moderate_video(video_path)


# Convenience function (async)
async def moderate_video_async(video_path: str, max_workers: int = 120) -> VideoModerationResult:
    """
    Convenience function to moderate a video (async with parallel workers).

    For a 60s video at 2fps = 120 frames, we can spawn 120 workers.

    Usage:
        result = await moderate_video_async("/path/to/video.mp4")
        print(f"Decision: {result.decision}")
    """
    pipeline = VideoModerationPipeline(use_async=True, max_async_workers=max_workers)
    return await pipeline.moderate_video_async(video_path)


