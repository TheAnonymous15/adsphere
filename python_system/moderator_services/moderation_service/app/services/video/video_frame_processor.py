"""
Video Frame Processor - Analyzes extracted video frames
Third stage of video moderation pipeline

Input: List of frame paths
Output: Frame analysis results (objects, scenes, text, NSFW, violence, etc.)
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up paths for model_registry import
# Path: video/video_frame_processor.py -> video -> services -> app -> moderation_service -> moderator_services
CURRENT_DIR = Path(__file__).parent.resolve()
SERVICES_DIR = CURRENT_DIR.parent.resolve()
APP_DIR = SERVICES_DIR.parent.resolve()
MODERATION_SERVICE_DIR = APP_DIR.parent.resolve()
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent.resolve()

for _path in [str(MODERATOR_SERVICES_DIR), str(MODERATION_SERVICE_DIR), str(APP_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from model_registry import ensure_models, get_model_path

# Ensure required models are available
REQUIRED_MODELS = ['yolov8n', 'ultralytics']
if not ensure_models(REQUIRED_MODELS, verbose=False):
    print(f"⚠ VideoFrameProcessor: Some models not available: {REQUIRED_MODELS}")


@dataclass
class FrameAnalysis:
    """Analysis result for a single frame"""
    frame_path: str
    frame_index: int
    timestamp: float  # Approximate timestamp in video

    # Detection results
    objects: List[Dict] = field(default_factory=list)
    text_detected: str = ""
    nsfw_score: float = 0.0
    violence_score: float = 0.0
    weapon_score: float = 0.0
    blood_score: float = 0.0

    # Scene analysis
    scene_type: str = ""
    scene_confidence: float = 0.0

    # Flags
    flags: List[str] = field(default_factory=list)


@dataclass
class VideoFrameProcessorResult:
    """Aggregated result from processing all frames"""
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

    # Scene types detected
    scene_types: List[str] = field(default_factory=list)

    # All flags raised
    all_flags: List[str] = field(default_factory=list)

    # Individual frame analyses
    frame_results: List[FrameAnalysis] = field(default_factory=list)

    # Category scores for decision engine
    category_scores: Dict[str, float] = field(default_factory=dict)

    # AI sources used
    ai_sources: Dict[str, Any] = field(default_factory=dict)

    # Processing stats
    processing_time_ms: float = 0.0

    error: Optional[str] = None


class VideoFrameProcessor:
    """
    Processes extracted video frames through multiple AI models.

    Analysis performed on each frame:
    1. NSFW Detection - Nudity, sexual content
    2. Violence Detection - Fighting, assault
    3. Weapon Detection - Guns, knives
    4. Blood Detection - Gore, injury
    5. OCR - Text extraction
    6. Object Detection - General objects
    """

    def __init__(self, parallel: bool = True, max_workers: int = 4):
        """
        Initialize frame processor with all detection models.
        """
        self.parallel = parallel
        self.max_workers = max_workers

        # Initialize detectors
        self.nsfw_detector = None
        self.violence_detector = None
        self.weapon_detector = None
        self.blood_detector = None
        self.ocr_service = None
        self.object_detector = None

        self._load_models()

    def _load_models(self):
        """Load all detection models"""
        # NSFW Detector
        try:
            from app.services.nsfw_detector import NSFWDetector
            self.nsfw_detector = NSFWDetector()
        except Exception as e:
            print(f"⚠ NSFW detector not available: {e}")

        # Violence Detector
        try:
            from app.services.yolo_violence import ViolenceDetector
            self.violence_detector = ViolenceDetector()
        except Exception as e:
            print(f"⚠ Violence detector not available: {e}")

        # Weapon Detector
        try:
            from app.services.yolo_weapons import WeaponDetector
            self.weapon_detector = WeaponDetector()
        except Exception as e:
            print(f"⚠ Weapon detector not available: {e}")

        # Blood Detector
        try:
            from app.services.blood_detector import BloodDetector
            self.blood_detector = BloodDetector()
        except Exception as e:
            print(f"⚠ Blood detector not available: {e}")

        # OCR Service
        try:
            from app.services.ocr_paddle import OCRService
            self.ocr_service = OCRService()
        except Exception as e:
            print(f"⚠ OCR service not available: {e}")

        # Object Detector (use YOLO)
        try:
            from ultralytics import YOLO
            model_path = get_model_path('yolov8n')
            if model_path:
                self.object_detector = YOLO(str(model_path))
            else:
                self.object_detector = YOLO('yolov8n.pt')
        except Exception as e:
            print(f"⚠ Object detector not available: {e}")

    def process_frames(
        self,
        frame_paths: List[str],
        fps_used: float = 2.0,
        skip_ocr: bool = False
    ) -> VideoFrameProcessorResult:
        """
        Process all frames through detection models.
        """
        import time
        start_time = time.time()

        if not frame_paths:
            return VideoFrameProcessorResult(
                success=False,
                frames_analyzed=0,
                frames_flagged=0,
                error="No frames provided"
            )

        frame_results = []

        if self.parallel and len(frame_paths) > 1:
            frame_results = self._process_parallel(frame_paths, fps_used, skip_ocr)
        else:
            frame_results = self._process_sequential(frame_paths, fps_used, skip_ocr)

        # Aggregate results
        result = self._aggregate_results(frame_results)
        result.processing_time_ms = (time.time() - start_time) * 1000

        return result

    def _process_sequential(self, frame_paths: List[str], fps_used: float, skip_ocr: bool) -> List[FrameAnalysis]:
        """Process frames one by one"""
        results = []

        for i, frame_path in enumerate(frame_paths):
            timestamp = i / fps_used if fps_used > 0 else i
            analysis = self._analyze_single_frame(frame_path, i, timestamp, skip_ocr)
            results.append(analysis)

            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(frame_paths)} frames...")

        return results

    def _process_parallel(self, frame_paths: List[str], fps_used: float, skip_ocr: bool) -> List[FrameAnalysis]:
        """Process frames in parallel"""
        results = [None] * len(frame_paths)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}

            for i, frame_path in enumerate(frame_paths):
                timestamp = i / fps_used if fps_used > 0 else i
                future = executor.submit(
                    self._analyze_single_frame,
                    frame_path, i, timestamp, skip_ocr
                )
                futures[future] = i

            completed = 0
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    print(f"⚠ Frame {idx} failed: {e}")
                    results[idx] = FrameAnalysis(
                        frame_path=frame_paths[idx],
                        frame_index=idx,
                        timestamp=idx / fps_used if fps_used > 0 else idx
                    )

                completed += 1
                if completed % 20 == 0:
                    print(f"  Processed {completed}/{len(frame_paths)} frames...")

        return [r for r in results if r is not None]

    def _analyze_single_frame(
        self,
        frame_path: str,
        frame_index: int,
        timestamp: float,
        skip_ocr: bool
    ) -> FrameAnalysis:
        """Analyze a single frame with all detectors."""
        analysis = FrameAnalysis(
            frame_path=frame_path,
            frame_index=frame_index,
            timestamp=timestamp
        )

        if not os.path.exists(frame_path):
            return analysis

        flags = []

        # 1. NSFW Detection
        if self.nsfw_detector:
            try:
                nsfw_result = self.nsfw_detector.analyze_image(frame_path)
                analysis.nsfw_score = max(
                    nsfw_result.get('nudity', 0.0),
                    nsfw_result.get('sexual_content', 0.0)
                )
                if analysis.nsfw_score > 0.5:
                    flags.append('nsfw')
            except:
                pass

        # 2. Violence Detection
        if self.violence_detector:
            try:
                violence_result = self.violence_detector.detect(frame_path)
                analysis.violence_score = violence_result.get('violence_score', 0.0)
                if analysis.violence_score > 0.5:
                    flags.append('violence')
            except:
                pass

        # 3. Weapon Detection
        if self.weapon_detector:
            try:
                weapon_result = self.weapon_detector.detect(frame_path)
                analysis.weapon_score = weapon_result.get('weapon_score', 0.0)
                if weapon_result.get('weapon_detected', False):
                    flags.append('weapon')
            except:
                pass

        # 4. Blood Detection
        if self.blood_detector:
            try:
                blood_result = self.blood_detector.detect(frame_path)
                analysis.blood_score = blood_result.get('blood_score', 0.0)
                if analysis.blood_score > 0.5:
                    flags.append('blood')
            except:
                pass

        # 5. OCR - Text extraction
        if self.ocr_service and not skip_ocr:
            try:
                ocr_result = self.ocr_service.extract_text(frame_path)
                analysis.text_detected = ocr_result.get('text', '')
            except:
                pass

        # 6. Object Detection
        if self.object_detector:
            try:
                predictions = self.object_detector(frame_path, verbose=False)
                for result in predictions:
                    if result.boxes is not None:
                        for box in result.boxes:
                            cls_id = int(box.cls[0])
                            conf = float(box.conf[0])
                            cls_name = result.names.get(cls_id, "")
                            if conf > 0.3:
                                analysis.objects.append({
                                    'class': cls_name,
                                    'confidence': conf
                                })
            except:
                pass

        analysis.flags = flags

        return analysis

    def _aggregate_results(self, frame_results: List[FrameAnalysis]) -> VideoFrameProcessorResult:
        """Aggregate results from all frames."""
        if not frame_results:
            return VideoFrameProcessorResult(
                success=False,
                frames_analyzed=0,
                frames_flagged=0,
                error="No frames analyzed"
            )

        # Initialize aggregation
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
                all_objects.add(obj['class'])

            if frame.flags:
                frames_flagged += 1
                all_flags.update(frame.flags)

        # Build category scores
        category_scores = {
            'nudity': max_nsfw,
            'sexual_content': max_nsfw,
            'violence': max_violence,
            'weapons': max_weapon,
            'blood': max_blood
        }

        # Build AI sources
        ai_sources = {
            'nsfw': {'max_score': max_nsfw, 'frames_flagged': sum(1 for f in frame_results if f.nsfw_score > 0.5)},
            'violence': {'max_score': max_violence, 'frames_flagged': sum(1 for f in frame_results if f.violence_score > 0.5)},
            'weapons': {'max_score': max_weapon, 'frames_flagged': sum(1 for f in frame_results if f.weapon_score > 0.3)},
            'blood': {'max_score': max_blood, 'frames_flagged': sum(1 for f in frame_results if f.blood_score > 0.5)},
            'ocr': {'text_length': len('\n'.join(all_text)), 'frames_with_text': sum(1 for f in frame_results if f.text_detected)}
        }

        return VideoFrameProcessorResult(
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


# Convenience function
def process_video_frames(
    frame_paths: List[str],
    fps: float = 2.0,
    parallel: bool = True
) -> VideoFrameProcessorResult:
    """Convenience function to process video frames."""
    processor = VideoFrameProcessor(parallel=parallel)
    return processor.process_frames(frame_paths, fps)

