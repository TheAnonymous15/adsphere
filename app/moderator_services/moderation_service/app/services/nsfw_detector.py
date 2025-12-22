"""
NSFW detection combining OpenNSFW2 and NudeNet
"""
import sys
from pathlib import Path
from typing import Dict
import os

# Add parent path for model_registry import
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
from model_registry import ensure_models

# Ensure required models are available (nudenet is optional)
REQUIRED_MODELS = ['nudenet']
ensure_models(REQUIRED_MODELS, verbose=False)  # Don't fail if not available


class NSFWDetector:
    """
    Combined NSFW detection using multiple models.

    Models:
    - OpenNSFW2: General nudity detection
    - NudeNet: Explicit content classification
    """

    def __init__(self):
        """Initialize NSFW detection models"""
        self.open_nsfw_model = None
        self.nudenet_classifier = None
        self._load_models()

    def _load_models(self):
        """Lazy load models"""
        try:
            import open_nsfw2 as on2
            self.open_nsfw_model = on2.make_open_nsfw_model()
            print("✓ OpenNSFW2 model loaded")
        except Exception as e:
            print(f"⚠ OpenNSFW2 not available: {e}")

        try:
            from nudenet import NudeClassifier
            self.nudenet_classifier = NudeClassifier()
            print("✓ NudeNet classifier loaded")
        except Exception as e:
            print(f"⚠ NudeNet not available: {e}")

    def analyze_image(self, image_path: str) -> Dict[str, float]:
        """
        Analyze image for NSFW content.

        Args:
            image_path: Path to image file

        Returns:
            Dict with scores:
                - nudity: Overall nudity score
                - sexual_content: Explicit sexual content score
        """
        if not os.path.exists(image_path):
            return {'nudity': 0.0, 'sexual_content': 0.0}

        scores = {'nudity': 0.0, 'sexual_content': 0.0}

        # OpenNSFW2
        if self.open_nsfw_model:
            try:
                import open_nsfw2 as on2
                nsfw_prob = on2.predict_image(self.open_nsfw_model, image_path)
                scores['nudity'] = float(nsfw_prob)
            except Exception as e:
                print(f"OpenNSFW2 error: {e}")

        # NudeNet
        if self.nudenet_classifier:
            try:
                result = self.nudenet_classifier.classify(image_path)
                # NudeNet returns dict like: {image_path: {'safe': 0.8, 'unsafe': 0.2}}
                if image_path in result:
                    unsafe_score = result[image_path].get('unsafe', 0.0)
                    scores['sexual_content'] = float(unsafe_score)
                    # Use max of both models
                    scores['nudity'] = max(scores['nudity'], float(unsafe_score))
            except Exception as e:
                print(f"NudeNet error: {e}")

        return scores

    def analyze_video_frames(self, frame_paths: list) -> Dict[str, float]:
        """
        Analyze multiple video frames and aggregate.

        Args:
            frame_paths: List of paths to frame images

        Returns:
            Aggregated scores (max across all frames)
        """
        max_nudity = 0.0
        max_sexual = 0.0

        for frame_path in frame_paths:
            frame_scores = self.analyze_image(frame_path)
            max_nudity = max(max_nudity, frame_scores['nudity'])
            max_sexual = max(max_sexual, frame_scores['sexual_content'])

        return {
            'nudity': max_nudity,
            'sexual_content': max_sexual
        }

