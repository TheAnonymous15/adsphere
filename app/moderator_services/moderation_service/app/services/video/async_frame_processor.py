"""
Async Video Frame Processor - Parallel frame analysis using BatchCoordinator
Processes all extracted frames concurrently for maximum speed

For a 60s video at 2fps = 120 frames
Uses BatchCoordinator to process frames in batches of 8 through 5 parallel pipelines
"""
import os
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class FrameAnalysis:
    """Analysis result for a single frame"""
    frame_path: str
    frame_index: int
    timestamp: float

    # Detection results
    objects: List[Dict] = field(default_factory=list)
    text_detected: str = ""
    nsfw_score: float = 0.0
    violence_score: float = 0.0
    weapon_score: float = 0.0
    blood_score: float = 0.0

    # Flags
    flags: List[str] = field(default_factory=list)

    # Processing info
    processing_time_ms: float = 0.0
    batch_id: int = 0


@dataclass
class AsyncFrameProcessorResult:
    """Aggregated result from async processing"""
    success: bool
    frames_analyzed: int
    frames_flagged: int

    # Aggregated scores (max across all frames)
    max_nsfw_score: float = 0.0
    max_violence_score: float = 0.0
    max_weapon_score: float = 0.0
    max_blood_score: float = 0.0

    # Combined text from all frames (OCR)
    all_text: str = ""

    # All detected objects
    all_objects: List[str] = field(default_factory=list)

    # All flags raised
    all_flags: List[str] = field(default_factory=list)

    # Individual frame analyses
    frame_results: List[FrameAnalysis] = field(default_factory=list)

    # Category scores for decision engine
    category_scores: Dict[str, float] = field(default_factory=dict)

    # AI sources used
    ai_sources: Dict[str, Any] = field(default_factory=dict)

    # Processing stats
    total_processing_time_ms: float = 0.0
    avg_frame_time_ms: float = 0.0
    batches_processed: int = 0
    batch_size: int = 8

    error: Optional[str] = None


class AsyncVideoFrameProcessor:
    """
    Async video frame processor using BatchCoordinator.

    For 120 frames from a 60s video:
    - Frames are processed in batches of 8
    - Each batch goes through 5 parallel pipelines (OCR, NSFW, Violence, Weapons, Policy)
    - Results are aggregated for final decision

    Pipeline per batch:
    ┌─────────────────────────────────────────────────────────────────┐
    │  Batch of 8 Frames                                              │
    │       │                                                         │
    │       ├──► OCR Worker (PaddleOCR)                               │
    │       ├──► NSFW Worker (NudeNet)                                │
    │       ├──► Violence Worker (YOLO + Blood)                       │
    │       ├──► Weapons Worker (YOLO + Classifier)                   │
    │       └──► Policy Worker (Text Rules + Detoxify)                │
    │                                                                 │
    │  All 5 pipelines run in PARALLEL                                │
    └─────────────────────────────────────────────────────────────────┘

    Usage:
        processor = AsyncVideoFrameProcessor(batch_size=8)
        result = await processor.process_frames_async(frame_paths)
    """

    def __init__(
        self,
        batch_size: int = 8,
        max_workers: int = 4
    ):
        """
        Initialize async frame processor.

        Args:
            batch_size: Frames per batch (default: 8 for GPU efficiency)
            max_workers: Thread pool workers for model inference
        """
        self.batch_size = batch_size
        self.max_workers = max_workers
        self._coordinator = None

    async def _get_coordinator(self):
        """Get or create BatchCoordinator instance."""
        if self._coordinator is None:
            from app.workers.batch_coordinator import BatchCoordinator
            self._coordinator = BatchCoordinator(
                batch_size=self.batch_size,
                max_workers=self.max_workers
            )
        return self._coordinator

    async def process_frames_async(
        self,
        frame_paths: List[str],
        fps_used: float = 2.0
    ) -> AsyncFrameProcessorResult:
        """
        Process all frames asynchronously using BatchCoordinator.

        Args:
            frame_paths: List of paths to frame images
            fps_used: FPS used for extraction (for timestamp calculation)

        Returns:
            AsyncFrameProcessorResult with aggregated analysis
        """
        import time
        start_time = time.time()

        if not frame_paths:
            return AsyncFrameProcessorResult(
                success=False,
                frames_analyzed=0,
                frames_flagged=0,
                error="No frames provided"
            )

        num_frames = len(frame_paths)
        num_batches = (num_frames + self.batch_size - 1) // self.batch_size

        print(f"🚀 Processing {num_frames} frames in {num_batches} batches of {self.batch_size}...")

        # Get coordinator
        coordinator = await self._get_coordinator()

        # Start workers in background
        worker_task = asyncio.create_task(coordinator.run_workers())

        try:
            # Schedule all frames
            task_ids = []
            for i, frame_path in enumerate(frame_paths):
                if not os.path.exists(frame_path):
                    print(f"  ⚠ Frame not found: {frame_path}")
                    continue

                task_id = f"frame-{i:05d}"
                task_ids.append((task_id, i, frame_path))

                # Read frame bytes
                with open(frame_path, 'rb') as f:
                    frame_bytes = f.read()

                await coordinator.schedule(task_id, frame_bytes, "video_frame")

            # Wait for all results
            frame_results = []
            for task_id, frame_index, frame_path in task_ids:
                result = await coordinator.wait_for_result(task_id, timeout=60.0)

                if result:
                    # Convert coordinator result to FrameAnalysis
                    timestamp = frame_index / fps_used if fps_used > 0 else frame_index

                    analysis = FrameAnalysis(
                        frame_path=frame_path,
                        frame_index=frame_index,
                        timestamp=timestamp,
                        text_detected=result.get("ocr_text", ""),
                        nsfw_score=result.get("category_scores", {}).get("nsfw", 0.0),
                        violence_score=result.get("category_scores", {}).get("violence", 0.0),
                        weapon_score=result.get("category_scores", {}).get("weapons", 0.0),
                        blood_score=result.get("category_scores", {}).get("blood", 0.0),
                        flags=result.get("flags", []),
                        batch_id=frame_index // self.batch_size
                    )
                    frame_results.append(analysis)

                # Progress update
                if (len(frame_results) % 20 == 0):
                    print(f"  Processed {len(frame_results)}/{num_frames} frames...")

            # Aggregate results
            aggregated = self._aggregate_results(frame_results)

            total_time = (time.time() - start_time) * 1000
            aggregated.total_processing_time_ms = total_time
            aggregated.avg_frame_time_ms = total_time / num_frames if num_frames > 0 else 0
            aggregated.batches_processed = num_batches
            aggregated.batch_size = self.batch_size

            print(f"✅ Processed {num_frames} frames in {total_time:.0f}ms ({aggregated.avg_frame_time_ms:.1f}ms/frame)")
            print(f"   Batches: {num_batches}, Flags: {len(aggregated.all_flags)}")

            return aggregated

        finally:
            # Shutdown coordinator
            await coordinator.shutdown()
            worker_task.cancel()
            self._coordinator = None

    def _aggregate_results(self, frame_results: List[FrameAnalysis]) -> AsyncFrameProcessorResult:
        """Aggregate results from all frames."""
        if not frame_results:
            return AsyncFrameProcessorResult(
                success=False,
                frames_analyzed=0,
                frames_flagged=0,
                error="No frames analyzed"
            )

        max_nsfw = 0.0
        max_violence = 0.0
        max_weapon = 0.0
        max_blood = 0.0
        all_text = []
        all_objects = set()
        all_flags = set()
        frames_flagged = 0

        for frame in frame_results:
            max_nsfw = max(max_nsfw, frame.nsfw_score)
            max_violence = max(max_violence, frame.violence_score)
            max_weapon = max(max_weapon, frame.weapon_score)
            max_blood = max(max_blood, frame.blood_score)

            if frame.text_detected:
                all_text.append(frame.text_detected)

            for obj in frame.objects:
                if isinstance(obj, dict):
                    all_objects.add(obj.get('class', ''))
                else:
                    all_objects.add(str(obj))

            if frame.flags:
                frames_flagged += 1
                all_flags.update(frame.flags)

        category_scores = {
            'nudity': max_nsfw,
            'sexual_content': max_nsfw,
            'violence': max_violence,
            'weapons': max_weapon,
            'blood': max_blood
        }

        ai_sources = {
            'nsfw': {'max_score': max_nsfw, 'frames_flagged': sum(1 for f in frame_results if f.nsfw_score > 0.5)},
            'violence': {'max_score': max_violence, 'frames_flagged': sum(1 for f in frame_results if f.violence_score > 0.5)},
            'weapons': {'max_score': max_weapon, 'frames_flagged': sum(1 for f in frame_results if f.weapon_score > 0.3)},
            'blood': {'max_score': max_blood, 'frames_flagged': sum(1 for f in frame_results if f.blood_score > 0.5)},
            'ocr': {'text_length': len('\n'.join(all_text)), 'frames_with_text': sum(1 for f in frame_results if f.text_detected)}
        }

        return AsyncFrameProcessorResult(
            success=True,
            frames_analyzed=len(frame_results),
            frames_flagged=frames_flagged,
            max_nsfw_score=max_nsfw,
            max_violence_score=max_violence,
            max_weapon_score=max_weapon,
            max_blood_score=max_blood,
            all_text='\n\n'.join(all_text),
            all_objects=list(all_objects),
            all_flags=list(all_flags),
            frame_results=frame_results,
            category_scores=category_scores,
            ai_sources=ai_sources
        )


# Convenience async function
async def process_frames_async(
    frame_paths: List[str],
    fps: float = 2.0,
    batch_size: int = 8
) -> AsyncFrameProcessorResult:
    """
    Convenience function to process frames asynchronously using BatchCoordinator.

    Usage:
        result = await process_frames_async(frame_paths, fps=2.0, batch_size=8)
    """
    processor = AsyncVideoFrameProcessor(batch_size=batch_size)
    return await processor.process_frames_async(frame_paths, fps)

