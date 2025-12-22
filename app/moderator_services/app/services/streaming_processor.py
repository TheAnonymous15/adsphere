"""
Streaming Support with Chunk Processing and Sliding Windows
Process large videos in chunks with overlapping windows
Optimized for memory efficiency and real-time processing
"""

import os
import time
import subprocess
import hashlib
from typing import Dict, List, Optional, Iterator, Tuple, Callable
from dataclasses import dataclass
from pathlib import Path
import json
from threading import Thread, Lock
from queue import Queue, Empty
import tempfile


@dataclass
class Chunk:
    """Represents a video/audio chunk"""
    chunk_id: str
    start_time: float
    end_time: float
    duration: float
    file_path: str
    frame_paths: List[str]
    metadata: Dict


@dataclass
class ChunkResult:
    """Result from processing a chunk"""
    chunk_id: str
    decision: str
    risk_level: str
    scores: Dict[str, float]
    flags: List[str]
    processing_time: float


class StreamChunker:
    """
    Splits streams into overlapping chunks for processing
    """

    def __init__(self,
                 chunk_duration: float = 10.0,
                 overlap_duration: float = 2.0,
                 fps: int = 2):
        """
        Args:
            chunk_duration: Duration of each chunk in seconds
            overlap_duration: Overlap between chunks in seconds
            fps: Frames per second to extract
        """
        self.chunk_duration = chunk_duration
        self.overlap_duration = overlap_duration
        self.fps = fps
        self.temp_dir = tempfile.mkdtemp(prefix="stream_chunks_")

    def chunk_video(self, video_path: str) -> Iterator[Chunk]:
        """
        Split video into overlapping chunks

        Yields:
            Chunk objects
        """
        # Get video duration
        duration = self._get_video_duration(video_path)

        if duration <= 0:
            raise ValueError(f"Invalid video duration: {duration}")

        # Calculate chunk positions
        step = self.chunk_duration - self.overlap_duration
        start_time = 0.0
        chunk_index = 0

        while start_time < duration:
            end_time = min(start_time + self.chunk_duration, duration)
            actual_duration = end_time - start_time

            # Generate chunk ID
            chunk_id = hashlib.md5(
                f"{video_path}_{start_time}_{end_time}".encode()
            ).hexdigest()[:16]

            # Extract chunk
            chunk_file = os.path.join(self.temp_dir, f"chunk_{chunk_index:04d}.mp4")
            self._extract_chunk(video_path, start_time, actual_duration, chunk_file)

            # Extract frames from chunk
            frame_paths = self._extract_frames(chunk_file, self.fps)

            # Create chunk object
            chunk = Chunk(
                chunk_id=chunk_id,
                start_time=start_time,
                end_time=end_time,
                duration=actual_duration,
                file_path=chunk_file,
                frame_paths=frame_paths,
                metadata={
                    'chunk_index': chunk_index,
                    'total_duration': duration,
                    'fps': self.fps
                }
            )

            yield chunk

            # Move to next chunk
            start_time += step
            chunk_index += 1

    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration using ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                return float(result.stdout.strip())
            else:
                print(f"⚠ Error getting video duration: {result.stderr}")
                return 0.0

        except Exception as e:
            print(f"⚠ Error getting video duration: {e}")
            return 0.0

    def _extract_chunk(self,
                      video_path: str,
                      start_time: float,
                      duration: float,
                      output_path: str):
        """Extract video chunk using ffmpeg"""
        try:
            cmd = [
                'ffmpeg',
                '-ss', str(start_time),
                '-t', str(duration),
                '-i', video_path,
                '-c', 'copy',
                '-y',
                output_path
            ]

            subprocess.run(
                cmd,
                capture_output=True,
                timeout=30,
                check=True
            )

        except subprocess.TimeoutExpired:
            print(f"⚠ Timeout extracting chunk at {start_time}s")
        except subprocess.CalledProcessError as e:
            print(f"⚠ Error extracting chunk: {e.stderr}")
        except Exception as e:
            print(f"⚠ Error extracting chunk: {e}")

    def _extract_frames(self, video_path: str, fps: int) -> List[str]:
        """Extract frames from video chunk"""
        frames_dir = os.path.join(self.temp_dir, f"frames_{Path(video_path).stem}")
        os.makedirs(frames_dir, exist_ok=True)

        try:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f'fps={fps}',
                '-y',
                os.path.join(frames_dir, 'frame_%04d.jpg')
            ]

            subprocess.run(
                cmd,
                capture_output=True,
                timeout=60,
                check=True
            )

            # Get list of extracted frames
            frame_files = sorted([
                os.path.join(frames_dir, f)
                for f in os.listdir(frames_dir)
                if f.endswith('.jpg')
            ])

            return frame_files

        except Exception as e:
            print(f"⚠ Error extracting frames: {e}")
            return []

    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            print(f"✓ Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            print(f"⚠ Error cleaning up: {e}")


class SlidingWindowProcessor:
    """
    Process chunks with sliding window aggregation
    Combines results from overlapping chunks
    """

    def __init__(self, window_size: int = 3):
        """
        Args:
            window_size: Number of chunks in sliding window
        """
        self.window_size = window_size
        self.results_buffer: List[ChunkResult] = []
        self.lock = Lock()

    def add_result(self, result: ChunkResult) -> Optional[Dict]:
        """
        Add chunk result and return aggregated result if window is full

        Args:
            result: Chunk processing result

        Returns:
            Aggregated result or None if window not full
        """
        with self.lock:
            self.results_buffer.append(result)

            # If window is full, aggregate and return
            if len(self.results_buffer) >= self.window_size:
                aggregated = self._aggregate_window()

                # Slide window (remove oldest result)
                self.results_buffer.pop(0)

                return aggregated

            return None

    def flush(self) -> Optional[Dict]:
        """Flush remaining results"""
        with self.lock:
            if self.results_buffer:
                aggregated = self._aggregate_window()
                self.results_buffer.clear()
                return aggregated
            return None

    def _aggregate_window(self) -> Dict:
        """Aggregate results in current window"""
        if not self.results_buffer:
            return {}

        # Aggregate scores (max per category)
        all_scores = {}
        all_flags = set()

        for result in self.results_buffer:
            for category, score in result.scores.items():
                all_scores[category] = max(all_scores.get(category, 0), score)

            all_flags.update(result.flags)

        # Determine worst decision
        decisions = [r.decision for r in self.results_buffer]
        if 'block' in decisions:
            final_decision = 'block'
        elif 'review' in decisions:
            final_decision = 'review'
        else:
            final_decision = 'approve'

        # Determine worst risk level
        risk_order = {'safe': 0, 'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        risk_levels = [r.risk_level for r in self.results_buffer]
        final_risk = max(risk_levels, key=lambda r: risk_order.get(r, 0))

        return {
            'decision': final_decision,
            'risk_level': final_risk,
            'scores': all_scores,
            'flags': list(all_flags),
            'window_size': len(self.results_buffer),
            'chunks_processed': len(self.results_buffer)
        }


class StreamingProcessor:
    """
    Main streaming processor with chunk processing and worker pool
    """

    def __init__(self,
                 chunk_duration: float = 10.0,
                 overlap_duration: float = 2.0,
                 fps: int = 2,
                 num_workers: int = 2):
        """
        Args:
            chunk_duration: Chunk duration in seconds
            overlap_duration: Overlap between chunks
            fps: Frames per second to extract
            num_workers: Number of worker threads
        """
        self.chunker = StreamChunker(chunk_duration, overlap_duration, fps)
        self.window_processor = SlidingWindowProcessor(window_size=3)
        self.num_workers = num_workers

        # Work queue
        self.chunk_queue: Queue = Queue()
        self.result_queue: Queue = Queue()

        # Workers
        self.workers: List[Thread] = []
        self.processing = False

    def process_stream(self,
                      video_path: str,
                      process_chunk_func: Callable[[Chunk], ChunkResult],
                      progress_callback: Optional[Callable[[Dict], None]] = None) -> Dict:
        """
        Process video stream in chunks

        Args:
            video_path: Path to video file
            process_chunk_func: Function to process each chunk
            progress_callback: Optional callback for progress updates

        Returns:
            Final aggregated result
        """
        self.processing = True

        # Start workers
        for i in range(self.num_workers):
            worker = Thread(
                target=self._worker_loop,
                args=(process_chunk_func,),
                daemon=True
            )
            worker.start()
            self.workers.append(worker)

        # Generate and queue chunks
        total_chunks = 0
        for chunk in self.chunker.chunk_video(video_path):
            self.chunk_queue.put(chunk)
            total_chunks += 1

        # Signal workers to stop after processing
        for _ in range(self.num_workers):
            self.chunk_queue.put(None)

        # Collect results
        processed_chunks = 0
        aggregated_results = []

        while processed_chunks < total_chunks:
            try:
                result = self.result_queue.get(timeout=60)

                if result:
                    processed_chunks += 1

                    # Add to sliding window
                    windowed_result = self.window_processor.add_result(result)

                    if windowed_result:
                        aggregated_results.append(windowed_result)

                    # Progress callback
                    if progress_callback:
                        progress_callback({
                            'processed': processed_chunks,
                            'total': total_chunks,
                            'progress': processed_chunks / total_chunks if total_chunks > 0 else 0
                        })

            except Empty:
                print("⚠ Timeout waiting for results")
                break

        # Flush remaining results
        final_windowed = self.window_processor.flush()
        if final_windowed:
            aggregated_results.append(final_windowed)

        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)

        self.workers.clear()
        self.processing = False

        # Cleanup
        self.chunker.cleanup()

        # Return final aggregated result
        if aggregated_results:
            return self._aggregate_all_results(aggregated_results)
        else:
            return {
                'decision': 'error',
                'risk_level': 'unknown',
                'error': 'No results processed'
            }

    def _worker_loop(self, process_func: Callable):
        """Worker thread main loop"""
        while self.processing:
            try:
                chunk = self.chunk_queue.get(timeout=1)

                if chunk is None:
                    break

                # Process chunk
                start_time = time.time()
                result = process_func(chunk)
                result.processing_time = time.time() - start_time

                # Add result to queue
                self.result_queue.put(result)

            except Empty:
                continue
            except Exception as e:
                print(f"⚠ Error in worker: {e}")

    def _aggregate_all_results(self, results: List[Dict]) -> Dict:
        """Aggregate all windowed results into final result"""
        if not results:
            return {}

        # Take worst decision and risk level
        all_scores = {}
        all_flags = set()

        for result in results:
            for category, score in result['scores'].items():
                all_scores[category] = max(all_scores.get(category, 0), score)

            all_flags.update(result['flags'])

        # Final decision
        decisions = [r['decision'] for r in results]
        if 'block' in decisions:
            final_decision = 'block'
        elif 'review' in decisions:
            final_decision = 'review'
        else:
            final_decision = 'approve'

        # Final risk level
        risk_order = {'safe': 0, 'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        risk_levels = [r['risk_level'] for r in results]
        final_risk = max(risk_levels, key=lambda r: risk_order.get(r, 0))

        return {
            'decision': final_decision,
            'risk_level': final_risk,
            'scores': all_scores,
            'flags': list(all_flags),
            'total_windows': len(results),
            'streaming': True
        }


if __name__ == '__main__':
    # Test streaming processor
    import random

    def mock_process_chunk(chunk: Chunk) -> ChunkResult:
        """Mock chunk processor for testing"""
        time.sleep(random.uniform(0.1, 0.5))  # Simulate processing

        return ChunkResult(
            chunk_id=chunk.chunk_id,
            decision=random.choice(['approve', 'review', 'block']),
            risk_level=random.choice(['safe', 'low', 'medium', 'high']),
            scores={'nudity': random.random(), 'violence': random.random()},
            flags=[],
            processing_time=0
        )

    def progress_callback(progress: Dict):
        """Print progress"""
        print(f"Progress: {progress['processed']}/{progress['total']} "
              f"({progress['progress']:.1%})")

    # Note: This requires an actual video file to test
    # processor = StreamingProcessor(
    #     chunk_duration=10.0,
    #     overlap_duration=2.0,
    #     fps=2,
    #     num_workers=2
    # )
    #
    # result = processor.process_stream(
    #     'test_video.mp4',
    #     mock_process_chunk,
    #     progress_callback
    # )
    #
    # print("\nFinal Result:")
    # print(json.dumps(result, indent=2))

    print("✓ Streaming processor module loaded")
    print("  Features:")
    print("  - Chunk-based video processing")
    print("  - Sliding window aggregation")
    print("  - Multi-threaded workers")
    print("  - Memory-efficient streaming")

