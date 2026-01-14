"""
YOLO-based weapon detection + Image Classification
Detects guns, knives, and other weapons using multiple strategies
"""
import sys
from pathlib import Path
from typing import Dict, List
import os
import numpy as np

# Set up paths for model_registry import
# Path: services/yolo_weapons.py -> services -> app -> moderation_service -> moderator_services
CURRENT_DIR = Path(__file__).parent.resolve()
APP_DIR = CURRENT_DIR.parent.resolve()
MODERATION_SERVICE_DIR = APP_DIR.parent.resolve()
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent.resolve()

for _path in [str(MODERATOR_SERVICES_DIR), str(MODERATION_SERVICE_DIR), str(APP_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from model_registry import ensure_models, get_model_path

# Ensure required models are available
REQUIRED_MODELS = ['yolov8n', 'ultralytics', 'transformers', 'torch']
if not ensure_models(REQUIRED_MODELS, verbose=False):
    raise RuntimeError(f"WeaponDetector: Required models not available: {REQUIRED_MODELS}")


class WeaponDetector:
    """
    Multi-model weapon detection combining:
    1. YOLO object detection (knives, scissors, bats)
    2. Image classification for firearms
    3. Color/shape analysis for gun-like objects
    """

    # COCO classes that could be weapons
    COCO_WEAPON_CLASSES = {
        43: 'knife',
        76: 'scissors',
        34: 'baseball bat',
        39: 'bottle',  # Can be used as weapon
    }

    # Keywords that indicate weapons in image classification
    WEAPON_KEYWORDS = [
        'gun', 'pistol', 'rifle', 'firearm', 'revolver', 'handgun',
        'shotgun', 'machine gun', 'assault rifle', 'weapon', 'ammunition',
        'bullet', 'cartridge', 'knife', 'dagger', 'sword', 'blade',
        'machete', 'axe', 'hatchet', 'crossbow', 'bow', 'arrow'
    ]

    def __init__(self, model_path: str = None):
        """
        Initialize weapon detection models.
        """
        self.yolo_model = None
        self.classifier = None
        self.model_path = model_path
        self._load_models()

    def _load_models(self):
        """Load detection models"""
        # Load YOLO for object detection
        try:
            from ultralytics import YOLO
            model_path = get_model_path('yolov8n')
            if model_path:
                self.yolo_model = YOLO(str(model_path))
            else:
                self.yolo_model = YOLO('yolov8n.pt')
            print("✓ YOLOv8n loaded for object detection")
        except Exception as e:
            print(f"⚠ YOLO not available: {e}")
            self.yolo_model = None

        # Load image classifier for weapon identification
        try:
            from transformers import pipeline
            self.classifier = pipeline(
                "image-classification",
                model="google/vit-base-patch16-224",
                device=-1  # CPU
            )
            print("✓ Image classifier loaded for weapon identification")
        except Exception as e:
            print(f"⚠ Image classifier not available: {e}")
            self.classifier = None

    def detect(self, image_path: str, confidence_threshold: float = 0.25) -> Dict[str, any]:
        """
        Detect weapons using multiple strategies.
        """
        results = {
            "weapon_score": 0.0,
            "detections": [],
            "weapon_detected": False,
            "weapon_types": [],
            "analysis": {}
        }

        scores = []

        # Strategy 1: YOLO Object Detection
        yolo_score, yolo_detections = self._yolo_detect(image_path, confidence_threshold)
        results["analysis"]["yolo"] = {
            "score": yolo_score,
            "detections": yolo_detections
        }
        if yolo_score > 0:
            scores.append(yolo_score)
            results["detections"].extend(yolo_detections)

        # Strategy 2: Image Classification
        class_score, class_labels = self._classify_image(image_path)
        results["analysis"]["classification"] = {
            "score": class_score,
            "labels": class_labels
        }
        if class_score > 0:
            scores.append(class_score)
            for label in class_labels:
                if label not in [d["class"] for d in results["detections"]]:
                    results["detections"].append({
                        "class": label,
                        "confidence": class_score,
                        "source": "classifier"
                    })

        # Strategy 3: Gun-specific visual analysis
        gun_score = self._analyze_for_guns(image_path)
        results["analysis"]["gun_analysis"] = {"score": gun_score}
        if gun_score > 0.3:
            scores.append(gun_score)

        # Combine scores - take maximum
        if scores:
            results["weapon_score"] = max(scores)
            results["weapon_detected"] = results["weapon_score"] > 0.3

        # Extract weapon types
        results["weapon_types"] = list(set([d["class"] for d in results["detections"]]))

        return results

    def _yolo_detect(self, image_path: str, confidence_threshold: float) -> tuple:
        """YOLO-based detection for COCO weapon classes"""
        if self.yolo_model is None:
            return 0.0, []

        try:
            predictions = self.yolo_model(image_path, verbose=False)

            detections = []
            max_conf = 0.0

            for result in predictions:
                if result.boxes is None:
                    continue

                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    cls_name = result.names.get(cls_id, "")

                    # Check if it's a weapon-related class
                    if cls_id in self.COCO_WEAPON_CLASSES or cls_name.lower() in ['knife', 'scissors', 'baseball bat']:
                        if conf >= confidence_threshold:
                            detections.append({
                                "class": cls_name,
                                "confidence": conf,
                                "bbox": box.xyxy[0].tolist(),
                                "source": "yolo"
                            })
                            max_conf = max(max_conf, conf)

            return max_conf, detections

        except Exception as e:
            print(f"YOLO detection error: {e}")
            return 0.0, []

    def _classify_image(self, image_path: str) -> tuple:
        """Use image classification to identify weapons"""
        if self.classifier is None:
            return 0.0, []

        try:
            from PIL import Image
            image = Image.open(image_path).convert('RGB')

            predictions = self.classifier(image, top_k=10)

            weapon_labels = []
            max_score = 0.0

            for pred in predictions:
                label = pred['label'].lower()
                score = pred['score']

                # Check if label contains weapon keywords
                for keyword in self.WEAPON_KEYWORDS:
                    if keyword in label:
                        weapon_labels.append(pred['label'])
                        max_score = max(max_score, score)
                        break

            return max_score, weapon_labels

        except Exception as e:
            print(f"Classification error: {e}")
            return 0.0, []

    def _analyze_for_guns(self, image_path: str) -> float:
        """
        Visual analysis specifically for gun detection.
        Uses shape and color patterns common in firearms.
        """
        try:
            from PIL import Image
            import numpy as np

            img = Image.open(image_path).convert('RGB')
            img_array = np.array(img)

            # Analyze image characteristics
            height, width = img_array.shape[:2]

            # Convert to grayscale for edge analysis
            gray = np.mean(img_array, axis=2)

            # Look for dark, elongated objects (gun-like shapes)
            dark_pixels = gray < 80  # Dark pixels (guns are often black/dark)
            dark_ratio = np.sum(dark_pixels) / dark_pixels.size

            # Check for metallic colors (grays, blacks)
            r, g, b = img_array[:,:,0], img_array[:,:,1], img_array[:,:,2]

            # Metallic gray detection (R≈G≈B and mid-range values)
            gray_metal = (np.abs(r.astype(float) - g.astype(float)) < 30) & \
                        (np.abs(g.astype(float) - b.astype(float)) < 30) & \
                        (gray > 40) & (gray < 150)
            metal_ratio = np.sum(gray_metal) / gray_metal.size

            # Simple heuristic score
            gun_score = 0.0

            # If significant dark/metallic content
            if dark_ratio > 0.1 and metal_ratio > 0.05:
                gun_score = min(0.5, (dark_ratio + metal_ratio) * 1.5)

            # This is a basic heuristic - real gun detection needs proper ML model
            return gun_score

        except Exception as e:
            print(f"Gun analysis error: {e}")
            return 0.0

    # Keep backward compatibility
    @property
    def model(self):
        return self.yolo_model

    def detect_video_frames(self, frame_paths: List[str]) -> Dict[str, any]:
        """
        Detect weapons in multiple video frames.

        Args:
            frame_paths: List of paths to frame images

        Returns:
            Aggregated results (max score across frames)
        """
        max_score = 0.0
        all_detections = []
        weapon_types = set()
        frames_with_weapons = 0

        for frame_path in frame_paths:
            frame_result = self.detect(frame_path)

            if frame_result['weapon_score'] > max_score:
                max_score = frame_result['weapon_score']

            if frame_result['weapon_detected']:
                frames_with_weapons += 1
                all_detections.extend(frame_result['detections'])
                weapon_types.update(frame_result['weapon_types'])

        return {
            'weapon_score': max_score,
            'weapon_detected': max_score > 0.3,
            'frames_analyzed': len(frame_paths),
            'frames_with_weapons': frames_with_weapons,
            'weapon_types': list(weapon_types),
            'detections': all_detections[:10]  # Limit to 10 detections
        }

