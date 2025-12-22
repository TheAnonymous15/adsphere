"""
Content Analyzers
=================

Step 3+: Analyze image content for violations.

Includes:
- NSFW Detection
- Object Detection (weapons, drugs, etc.)
- Scene Classification
- Violence/Gore Detection
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent))

try:
    from model_registry import ensure_models, get_model_path
except ImportError:
    def ensure_models(models, verbose=False):
        return True
    def get_model_path(model_id):
        return None

from .models import ObjectDetection, SceneClassification, ImageViolationType


class NSFWAnalyzer:
    """
    NSFW content detection using multiple models.

    Models:
    - NudeNet: Explicit content classification
    - OpenNSFW2: General nudity detection
    """

    MODEL_REGISTRY_ID = 'nudenet'
    REQUIRED_MODELS = ['nudenet']

    # Thresholds
    NUDITY_THRESHOLD = 0.6
    EXPLICIT_THRESHOLD = 0.7

    def __init__(self):
        self.nudenet = None
        self.opennsfw = None
        self._load_models()

    def _load_models(self):
        """Load NSFW detection models"""
        # Try NudeNet
        if ensure_models(['nudenet'], verbose=False):
            try:
                from nudenet import NudeClassifier
                self.nudenet = NudeClassifier()
                print("✓ NudeNet loaded for NSFW detection")
            except Exception as e:
                print(f"⚠ NudeNet not available: {e}")

        # Try OpenNSFW2
        try:
            import open_nsfw2 as on2
            self.opennsfw = on2.make_open_nsfw_model()
            print("✓ OpenNSFW2 loaded")
        except Exception as e:
            print(f"⚠ OpenNSFW2 not available: {e}")

    def analyze(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze image for NSFW content.

        Returns:
            Dict with scores and classification
        """
        result = {
            'is_nsfw': False,
            'nudity_score': 0.0,
            'explicit_score': 0.0,
            'safe_score': 1.0,
            'categories': {},
            'violation': None
        }

        if not os.path.exists(image_path):
            return result

        scores = []

        # OpenNSFW2 analysis
        if self.opennsfw:
            try:
                import open_nsfw2 as on2
                nsfw_prob = on2.predict_image(self.opennsfw, image_path)
                result['nudity_score'] = float(nsfw_prob)
                scores.append(float(nsfw_prob))
            except Exception as e:
                print(f"⚠ OpenNSFW2 error: {e}")

        # NudeNet analysis
        if self.nudenet:
            try:
                classification = self.nudenet.classify(image_path)
                if image_path in classification:
                    scores_dict = classification[image_path]
                    result['safe_score'] = scores_dict.get('safe', 1.0)
                    result['explicit_score'] = scores_dict.get('unsafe', 0.0)
                    result['categories'] = scores_dict
                    scores.append(scores_dict.get('unsafe', 0.0))
            except Exception as e:
                print(f"⚠ NudeNet error: {e}")

        # Determine final classification
        if scores:
            max_score = max(scores)
            result['nudity_score'] = max(result['nudity_score'], max_score)

            if max_score >= self.EXPLICIT_THRESHOLD:
                result['is_nsfw'] = True
                result['violation'] = ImageViolationType.NUDITY
            elif max_score >= self.NUDITY_THRESHOLD:
                result['is_nsfw'] = True
                result['violation'] = ImageViolationType.NSFW

        return result


class ObjectDetector:
    """
    Object detection for identifying dangerous/prohibited items.

    Uses YOLOv8 for detection of:
    - Weapons (guns, knives)
    - Drugs/paraphernalia
    - Violence indicators
    """

    MODEL_REGISTRY_ID = 'yolov8n'
    REQUIRED_MODELS = ['yolov8n', 'ultralytics']

    # COCO classes of interest
    WEAPON_CLASSES = {43: 'knife', 76: 'scissors', 34: 'baseball bat'}
    PERSON_CLASS = 0

    # Additional weapon keywords for classifier
    WEAPON_KEYWORDS = [
        'gun', 'pistol', 'rifle', 'firearm', 'revolver', 'handgun',
        'shotgun', 'weapon', 'ammunition', 'bullet', 'knife', 'dagger',
        'sword', 'blade', 'machete', 'axe'
    ]

    def __init__(self):
        self.yolo = None
        self.classifier = None
        self._load_models()

    def _load_models(self):
        """Load detection models"""
        # Ensure models via registry
        ensure_models(self.REQUIRED_MODELS, verbose=False)

        # Load YOLO
        try:
            from ultralytics import YOLO
            model_path = get_model_path('yolov8n')
            if model_path:
                self.yolo = YOLO(str(model_path))
            else:
                self.yolo = YOLO('yolov8n.pt')
            print("✓ YOLOv8n loaded for object detection")
        except Exception as e:
            print(f"⚠ YOLO not available: {e}")

        # Load image classifier for weapon identification
        try:
            from transformers import pipeline
            self.classifier = pipeline(
                "image-classification",
                model="google/vit-base-patch16-224",
                device=-1
            )
            print("✓ ViT classifier loaded for weapon identification")
        except Exception as e:
            print(f"⚠ Image classifier not available: {e}")

    def detect(
        self,
        image_path: str,
        confidence_threshold: float = 0.25
    ) -> Dict[str, Any]:
        """
        Detect objects in image.

        Returns:
            Dict with detections and analysis
        """
        result = {
            'objects': [],
            'weapon_detected': False,
            'weapon_score': 0.0,
            'weapon_types': [],
            'person_count': 0,
            'violations': []
        }

        if not os.path.exists(image_path):
            return result

        # YOLO detection
        if self.yolo:
            yolo_result = self._yolo_detect(image_path, confidence_threshold)
            result['objects'].extend(yolo_result['objects'])
            result['person_count'] = yolo_result['person_count']

            if yolo_result['weapon_detected']:
                result['weapon_detected'] = True
                result['weapon_score'] = max(result['weapon_score'], yolo_result['weapon_score'])
                result['weapon_types'].extend(yolo_result['weapon_types'])

        # Classifier-based weapon detection
        if self.classifier:
            classifier_result = self._classifier_detect(image_path)
            if classifier_result['weapon_detected']:
                result['weapon_detected'] = True
                result['weapon_score'] = max(result['weapon_score'], classifier_result['weapon_score'])
                result['weapon_types'].extend(classifier_result['weapon_types'])

        # Add violations
        if result['weapon_detected']:
            result['violations'].append(ImageViolationType.WEAPONS)

        return result

    def _yolo_detect(
        self,
        image_path: str,
        confidence_threshold: float
    ) -> Dict[str, Any]:
        """Run YOLO object detection"""
        result = {
            'objects': [],
            'weapon_detected': False,
            'weapon_score': 0.0,
            'weapon_types': [],
            'person_count': 0
        }

        try:
            detections = self.yolo(image_path, verbose=False)

            for det in detections:
                boxes = det.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])

                    if conf < confidence_threshold:
                        continue

                    # Get label
                    label = det.names.get(cls_id, f'class_{cls_id}')

                    obj = ObjectDetection(
                        label=label,
                        confidence=conf,
                        bbox=box.xyxy[0].tolist(),
                        category='weapon' if cls_id in self.WEAPON_CLASSES else 'object'
                    )
                    result['objects'].append(obj)

                    # Check for weapons
                    if cls_id in self.WEAPON_CLASSES:
                        result['weapon_detected'] = True
                        result['weapon_score'] = max(result['weapon_score'], conf)
                        result['weapon_types'].append(label)

                    # Count people
                    if cls_id == self.PERSON_CLASS:
                        result['person_count'] += 1

        except Exception as e:
            print(f"⚠ YOLO detection error: {e}")

        return result

    def _classifier_detect(self, image_path: str) -> Dict[str, Any]:
        """Use image classifier to detect weapons"""
        result = {
            'weapon_detected': False,
            'weapon_score': 0.0,
            'weapon_types': []
        }

        try:
            predictions = self.classifier(image_path)

            for pred in predictions[:5]:
                label = pred['label'].lower()
                score = pred['score']

                # Check if label matches weapon keywords
                for keyword in self.WEAPON_KEYWORDS:
                    if keyword in label:
                        result['weapon_detected'] = True
                        result['weapon_score'] = max(result['weapon_score'], score)
                        result['weapon_types'].append(label)
                        break

        except Exception as e:
            print(f"⚠ Classifier detection error: {e}")

        return result


class SceneAnalyzer:
    """
    Scene classification and context analysis.

    Classifies:
    - Scene type (indoor, outdoor, etc.)
    - Context (violence, medical, etc.)
    - Mood/atmosphere
    """

    REQUIRED_MODELS = ['transformers', 'torch']

    # Scene categories that might indicate issues
    CONCERNING_SCENES = [
        'crime scene', 'violence', 'fight', 'blood', 'gore',
        'hospital', 'morgue', 'accident', 'disaster', 'war',
        'protest', 'riot'
    ]

    def __init__(self):
        self.classifier = None
        self.caption_model = None
        self._load_models()

    def _load_models(self):
        """Load scene analysis models"""
        ensure_models(self.REQUIRED_MODELS, verbose=False)

        # Scene classifier
        try:
            from transformers import pipeline
            self.classifier = pipeline(
                "image-classification",
                model="google/vit-base-patch16-224",
                device=-1
            )
            print("✓ Scene classifier loaded")
        except Exception as e:
            print(f"⚠ Scene classifier not available: {e}")

        # Image captioning for context
        try:
            from transformers import pipeline
            self.caption_model = pipeline(
                "image-to-text",
                model="Salesforce/blip-image-captioning-base",
                device=-1
            )
            print("✓ Image captioning model loaded")
        except Exception as e:
            print(f"⚠ Caption model not available: {e}")

    def analyze(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze scene content and context.

        Returns:
            Dict with scene classification and analysis
        """
        result = {
            'scene_type': 'unknown',
            'scene_confidence': 0.0,
            'caption': '',
            'attributes': [],
            'concerning': False,
            'concerning_reasons': []
        }

        if not os.path.exists(image_path):
            return result

        # Scene classification
        if self.classifier:
            try:
                predictions = self.classifier(image_path)
                if predictions:
                    result['scene_type'] = predictions[0]['label']
                    result['scene_confidence'] = predictions[0]['score']
                    result['attributes'] = [p['label'] for p in predictions[:5]]

                    # Check for concerning scenes
                    for pred in predictions[:10]:
                        label = pred['label'].lower()
                        for concerning in self.CONCERNING_SCENES:
                            if concerning in label:
                                result['concerning'] = True
                                result['concerning_reasons'].append(f"Scene: {label}")

            except Exception as e:
                print(f"⚠ Scene classification error: {e}")

        # Image captioning
        if self.caption_model:
            try:
                captions = self.caption_model(image_path)
                if captions:
                    result['caption'] = captions[0]['generated_text']

                    # Check caption for concerning content
                    caption_lower = result['caption'].lower()
                    for concerning in self.CONCERNING_SCENES:
                        if concerning in caption_lower:
                            result['concerning'] = True
                            result['concerning_reasons'].append(f"Caption mentions: {concerning}")

            except Exception as e:
                print(f"⚠ Captioning error: {e}")

        return result


class ViolenceDetector:
    """
    Violence and gore detection in images.
    """

    REQUIRED_MODELS = ['yolov8n', 'ultralytics']

    # Violence indicators
    VIOLENCE_KEYWORDS = [
        'fight', 'fighting', 'punch', 'kick', 'blood', 'wound',
        'injury', 'violence', 'attack', 'assault', 'gun', 'shooting'
    ]

    def __init__(self):
        self.classifier = None
        self._load_models()

    def _load_models(self):
        """Load violence detection models"""
        ensure_models(['transformers'], verbose=False)

        try:
            from transformers import pipeline
            self.classifier = pipeline(
                "image-classification",
                model="google/vit-base-patch16-224",
                device=-1
            )
            print("✓ Violence detector loaded")
        except Exception as e:
            print(f"⚠ Violence detector not available: {e}")

    def analyze(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze image for violence/gore.

        Returns:
            Dict with violence analysis
        """
        result = {
            'violence_detected': False,
            'violence_score': 0.0,
            'gore_detected': False,
            'gore_score': 0.0,
            'indicators': [],
            'violation': None
        }

        if not os.path.exists(image_path):
            return result

        if self.classifier:
            try:
                predictions = self.classifier(image_path)

                for pred in predictions[:10]:
                    label = pred['label'].lower()
                    score = pred['score']

                    for keyword in self.VIOLENCE_KEYWORDS:
                        if keyword in label:
                            result['indicators'].append(label)

                            if keyword in ['blood', 'wound', 'injury']:
                                result['gore_detected'] = True
                                result['gore_score'] = max(result['gore_score'], score)
                            else:
                                result['violence_detected'] = True
                                result['violence_score'] = max(result['violence_score'], score)

            except Exception as e:
                print(f"⚠ Violence analysis error: {e}")

        # Set violation type
        if result['gore_detected'] and result['gore_score'] > 0.5:
            result['violation'] = ImageViolationType.GORE
        elif result['violence_detected'] and result['violence_score'] > 0.5:
            result['violation'] = ImageViolationType.VIOLENCE

        return result

