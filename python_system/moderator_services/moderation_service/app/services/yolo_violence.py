"""
YOLO-based violence detection
Detects fights, physical altercations, aggressive behavior
"""
import sys
from pathlib import Path
from typing import Dict, List
import cv2
import numpy as np

# Set up paths for model_registry import
# Path: services/yolo_violence.py -> services -> app -> moderation_service -> moderator_services
CURRENT_DIR = Path(__file__).parent.resolve()
APP_DIR = CURRENT_DIR.parent.resolve()
MODERATION_SERVICE_DIR = APP_DIR.parent.resolve()
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent.resolve()

for _path in [str(MODERATOR_SERVICES_DIR), str(MODERATION_SERVICE_DIR), str(APP_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from model_registry import ensure_models, get_model_path, is_model_available

# Ensure required models are available
REQUIRED_MODELS = ['ultralytics', 'cv2']
if not ensure_models(REQUIRED_MODELS, verbose=False):
    raise RuntimeError(f"ViolenceDetector: Required models not available: {REQUIRED_MODELS}")


class ViolenceDetector:
    """
    YOLOv8-based violence detection.

    Detects:
    - Fighting
    - Physical altercations
    - Aggressive gestures
    - Weapons being used
    """

    def __init__(self, model_path: str = None):
        """
        Initialize violence detection model.

        Args:
            model_path: Path to YOLOv8 violence detection weights
        """
        self.model = None
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        """Lazy load YOLO model"""
        # Check if custom violence model is available
        if is_model_available('yolov8n_violence'):
            self.model_path = get_model_path('yolov8n_violence')
        elif self.model_path is None:
            # Try default location
            from app.core.config import settings
            import os
            self.model_path = os.path.join(
                settings.MODELS_DIR,
                settings.YOLO_VIOLENCE_MODEL
            )

        # Check if model file exists
        import os
        if not self.model_path or not os.path.exists(self.model_path):
            print(f"⚠ Violence model not found: {self.model_path}")
            print("  Custom violence model requires training on violence dataset")
            return

        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
            print(f"✓ Violence detection model loaded: {self.model_path}")
        except Exception as e:
            print(f"⚠ Failed to load violence model: {e}")

    def detect(self, image_path: str, confidence_threshold: float = 0.25) -> Dict[str, any]:
        """
        Detect violence in image.

        Args:
            image_path: Path to image file
            confidence_threshold: Minimum confidence for detection

        Returns:
            Dict with:
                - violence_score: Max confidence (0.0-1.0)
                - detections: List of detected violent actions
                - violence_detected: Boolean
        """
        if self.model is None:
            return {
                "violence_score": 0.0,
                "detections": [],
                "violence_detected": False,
                "error": "Model not loaded"
            }

        try:
            results = self.model(image_path, verbose=False)

            detections = []
            max_confidence = 0.0

            for result in results:
                if result.boxes is None:
                    continue

                for box in result.boxes:
                    conf = float(box.conf[0])
                    if conf < confidence_threshold:
                        continue

                    cls = int(box.cls[0])
                    class_name = result.names.get(cls, f"class_{cls}")

                    detections.append({
                        "class": class_name,
                        "confidence": conf,
                        "bbox": box.xyxy[0].tolist()
                    })

                    max_confidence = max(max_confidence, conf)

            return {
                "violence_score": max_confidence,
                "detections": detections,
                "violence_detected": max_confidence >= confidence_threshold,
                "num_detections": len(detections)
            }

        except Exception as e:
            print(f"Violence detection error: {e}")
            return {
                "violence_score": 0.0,
                "detections": [],
                "violence_detected": False,
                "error": str(e)
            }

    def detect_video_frames(self, frame_paths: List[str]) -> Dict[str, any]:
        """
        Detect violence across multiple video frames.

        Args:
            frame_paths: List of frame image paths

        Returns:
            Aggregated violence detection results
        """
        all_detections = []
        max_violence_score = 0.0
        frames_with_violence = 0

        for frame_path in frame_paths:
            result = self.detect(frame_path)

            if result.get("violence_detected"):
                frames_with_violence += 1
                all_detections.extend(result.get("detections", []))

            max_violence_score = max(
                max_violence_score,
                result.get("violence_score", 0.0)
            )

        total_frames = len(frame_paths)
        violence_ratio = frames_with_violence / total_frames if total_frames > 0 else 0.0

        return {
            "violence_score": max_violence_score,
            "violence_ratio": violence_ratio,
            "frames_with_violence": frames_with_violence,
            "total_frames": total_frames,
            "detections": all_detections,
            "violence_detected": max_violence_score > 0.25
        }

