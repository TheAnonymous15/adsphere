"""
Blood/gore detection using CNN
Detects graphic violence and gore content
"""
import sys
from pathlib import Path
from typing import Dict
import os
import numpy as np

# Set up paths for model_registry import
# Path: services/blood_detector.py -> services -> app -> moderation_service -> moderator_services
CURRENT_DIR = Path(__file__).parent.resolve()
APP_DIR = CURRENT_DIR.parent.resolve()
MODERATION_SERVICE_DIR = APP_DIR.parent.resolve()
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent.resolve()

for _path in [str(MODERATOR_SERVICES_DIR), str(MODERATION_SERVICE_DIR), str(APP_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from model_registry import ensure_models, get_model_path, is_model_available

# Ensure required models are available
REQUIRED_MODELS = ['torch']
if not ensure_models(REQUIRED_MODELS, verbose=False):
    print("⚠ BloodDetector: PyTorch not available")


class BloodDetector:
    """
    CNN-based blood/gore detection.

    Detects:
    - Blood
    - Gore
    - Graphic violence
    - Medical procedures (to distinguish from violence)
    """

    def __init__(self, model_path: str = None):
        """
        Initialize blood detection model.

        Args:
            model_path: Path to trained blood detection model
        """
        self.model = None
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        """Lazy load blood detection model"""
        # Check model_registry first
        if is_model_available('blood_cnn'):
            self.model_path = get_model_path('blood_cnn')
        elif self.model_path is None:
            from app.core.config import settings
            self.model_path = os.path.join(
                settings.MODELS_DIR,
                settings.BLOOD_MODEL
            )

        if not self.model_path or not os.path.exists(self.model_path):
            print(f"⚠ Blood detection model not found: {self.model_path}")
            print("  Train custom model or use pre-trained weights")
            return

        try:
            # Assuming PyTorch model
            import torch
            self.model = torch.load(self.model_path, map_location='cpu')
            self.model.eval()
            print(f"✓ Blood detection model loaded: {self.model_path}")
        except Exception as e:
            print(f"⚠ Failed to load blood model: {e}")

    def detect(self, image_path: str) -> Dict[str, any]:
        """
        Detect blood/gore in image.

        Args:
            image_path: Path to image file

        Returns:
            Dict with blood detection results
        """
        if self.model is None:
            # Fallback: use color-based heuristic
            return self._color_based_detection(image_path)

        try:
            import torch
            from PIL import Image
            import torchvision.transforms as transforms

            # Preprocess image
            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])

            image = Image.open(image_path).convert('RGB')
            input_tensor = transform(image).unsqueeze(0)

            # Inference
            with torch.no_grad():
                output = self.model(input_tensor)
                prob = torch.sigmoid(output).item()

            return {
                "blood_score": float(prob),
                "blood_detected": prob > 0.5,
                "method": "cnn"
            }

        except Exception as e:
            print(f"Blood detection error: {e}")
            return self._color_based_detection(image_path)

    def _color_based_detection(self, image_path: str) -> Dict[str, any]:
        """
        Fallback: Color-based blood detection (heuristic).

        Analyzes red color distribution that matches blood characteristics.
        """
        try:
            import cv2

            image = cv2.imread(image_path)
            if image is None:
                return {"blood_score": 0.0, "blood_detected": False, "error": "Failed to load image"}

            # Convert to HSV
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # Blood-like red color range in HSV
            # Hue: 0-10 and 160-180 (red spectrum)
            # Saturation: 100-255 (highly saturated)
            # Value: 50-200 (not too dark, not too bright)

            lower_red1 = np.array([0, 100, 50])
            upper_red1 = np.array([10, 255, 200])
            lower_red2 = np.array([160, 100, 50])
            upper_red2 = np.array([180, 255, 200])

            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask = cv2.bitwise_or(mask1, mask2)

            # Calculate percentage of blood-like pixels
            total_pixels = image.shape[0] * image.shape[1]
            blood_pixels = np.count_nonzero(mask)
            blood_ratio = blood_pixels / total_pixels

            # Normalize to 0-1 score
            blood_score = min(1.0, blood_ratio * 10)  # Scale up for sensitivity

            return {
                "blood_score": float(blood_score),
                "blood_detected": blood_score > 0.3,
                "blood_ratio": float(blood_ratio),
                "method": "color_heuristic"
            }

        except Exception as e:
            print(f"Color-based blood detection error: {e}")
            return {
                "blood_score": 0.0,
                "blood_detected": False,
                "error": str(e)
            }

    def detect_video_frames(self, frame_paths: list) -> Dict[str, any]:
        """
        Detect blood across multiple video frames.

        Args:
            frame_paths: List of frame image paths

        Returns:
            Aggregated blood detection results
        """
        max_blood_score = 0.0
        frames_with_blood = 0

        for frame_path in frame_paths:
            result = self.detect(frame_path)

            blood_score = result.get("blood_score", 0.0)
            max_blood_score = max(max_blood_score, blood_score)

            if result.get("blood_detected"):
                frames_with_blood += 1

        total_frames = len(frame_paths)
        blood_ratio = frames_with_blood / total_frames if total_frames > 0 else 0.0

        return {
            "blood_score": max_blood_score,
            "blood_ratio": blood_ratio,
            "frames_with_blood": frames_with_blood,
            "total_frames": total_frames,
            "blood_detected": max_blood_score > 0.3
        }

