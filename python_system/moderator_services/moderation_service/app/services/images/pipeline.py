"""
Image Moderation Pipeline
=========================

Main orchestrator for image moderation.

Pipeline Steps:
1. Security Scan - Check for embedded malicious data
2. OCR Extraction - Extract text from image
3. Text Moderation - Moderate extracted text (via text pipeline)
4. NSFW Detection - Check for adult content
5. Object Detection - Detect weapons, drugs, etc.
6. Scene Analysis - Classify scene and context
7. Violence Detection - Check for violence/gore
8. Aggregation - Combine all signals
9. Policy Evaluation - Make final decision
10. Explanation - Generate rationale
"""

import sys
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Set up paths for imports
# Path: images/pipeline.py -> images -> services -> app -> moderation_service -> moderator_services
CURRENT_DIR = Path(__file__).parent.resolve()
SERVICES_DIR = CURRENT_DIR.parent.resolve()
APP_DIR = SERVICES_DIR.parent.resolve()
MODERATION_SERVICE_DIR = APP_DIR.parent.resolve()
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent.resolve()

for _path in [str(MODERATOR_SERVICES_DIR), str(MODERATION_SERVICE_DIR), str(APP_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

try:
    from model_registry import ensure_models
except ImportError:
    def ensure_models(models, verbose=False):
        return True

from .models import (
    ImageModerationDecision,
    ImageViolationType,
    ImageModerationInput,
    ImageModerationResult,
    SecurityScanResult,
    OCRResult,
    ObjectDetection,
    SceneClassification
)
from .security_scanner import SecurityScanner
from .ocr_processor import ImageOCRProcessor
from .content_analyzers import NSFWAnalyzer, ObjectDetector, SceneAnalyzer, ViolenceDetector


class ImageModerationPipeline:
    """
    Complete image moderation pipeline.

    Orchestrates all analysis steps and makes final decision.
    """

    # Required base models
    REQUIRED_MODELS = ['transformers', 'torch', 'PIL']

    # Thresholds
    NSFW_BLOCK_THRESHOLD = 0.8
    NSFW_REVIEW_THRESHOLD = 0.5
    WEAPON_BLOCK_THRESHOLD = 0.7
    WEAPON_REVIEW_THRESHOLD = 0.4
    VIOLENCE_BLOCK_THRESHOLD = 0.7
    VIOLENCE_REVIEW_THRESHOLD = 0.4

    def __init__(self, enable_text_moderation: bool = True):
        """
        Initialize the image moderation pipeline.

        Args:
            enable_text_moderation: Whether to moderate extracted text
        """
        print("\n" + "="*60)
        print("  Initializing Image Moderation Pipeline")
        print("="*60 + "\n")

        self.enable_text_moderation = enable_text_moderation

        # Ensure required models
        ensure_models(self.REQUIRED_MODELS, verbose=False)

        # Initialize components
        self.security_scanner = SecurityScanner()
        self.ocr_processor = ImageOCRProcessor()
        self.nsfw_analyzer = NSFWAnalyzer()
        self.object_detector = ObjectDetector()
        self.scene_analyzer = SceneAnalyzer()
        self.violence_detector = ViolenceDetector()

        # Text moderation (imported lazily to avoid circular imports)
        self.text_moderator = None
        if enable_text_moderation:
            self._load_text_moderator()

        print("\n" + "="*60)
        print("  Image Moderation Pipeline Ready")
        print("="*60 + "\n")

    def _load_text_moderator(self):
        """Load text moderation pipeline"""
        try:
            from ..text import moderate_text
            self.text_moderator = moderate_text
            print("✓ Text moderation enabled for OCR content")
        except ImportError as e:
            print(f"⚠ Text moderation not available: {e}")
            self.text_moderator = None

    def moderate(self, input_data: ImageModerationInput) -> ImageModerationResult:
        """
        Run complete moderation pipeline on image.

        Args:
            input_data: ImageModerationInput with image path/data

        Returns:
            ImageModerationResult with decision and analysis
        """
        start_time = time.time()

        # Initialize result
        result = ImageModerationResult(
            decision=ImageModerationDecision.APPROVE,
            confidence=1.0
        )

        image_path = input_data.image_path

        # Validate image exists
        if not os.path.exists(image_path):
            result.decision = ImageModerationDecision.BLOCK
            result.confidence = 1.0
            result.explanation = "Image file not found"
            return result

        violations = []
        violation_scores = {}
        rationale = []
        models_used = []
        analyses = []

        # =========================================================
        # STEP 1: Security Scan
        # =========================================================
        print("  [1/7] Running security scan...")
        security_result = self.security_scanner.scan(image_path)
        result.security_scan = security_result
        analyses.append("security_scan")

        if not security_result.is_safe:
            violations.append(ImageViolationType.MALICIOUS_DATA)
            violation_scores['malicious_data'] = 1.0
            rationale.append(f"Security threat detected: {', '.join(security_result.warnings[:3])}")

            # Block immediately for security threats
            result.decision = ImageModerationDecision.BLOCK
            result.confidence = 0.99
            result.violations = violations
            result.violation_scores = violation_scores
            result.explanation = "Blocked: Security threat detected in image"
            result.detailed_rationale = rationale
            result.processing_time_ms = (time.time() - start_time) * 1000
            result.analyses_performed = analyses
            return result

        if security_result.has_embedded_data:
            rationale.append(f"Embedded data detected: {security_result.embedded_type}")

        # =========================================================
        # STEP 2: OCR Text Extraction
        # =========================================================
        print("  [2/7] Extracting text via OCR...")
        ocr_result = self.ocr_processor.extract_text(image_path)
        result.ocr_result = ocr_result
        analyses.append("ocr")

        if ocr_result.has_text:
            models_used.append("PaddleOCR")
            print(f"      Found {ocr_result.num_lines} lines of text")

        # =========================================================
        # STEP 3: Text Moderation (if text found)
        # =========================================================
        if ocr_result.has_text and self.text_moderator:
            print("  [3/7] Moderating extracted text...")
            analyses.append("text_moderation")

            try:
                text_result = self.text_moderator(
                    title=input_data.ad_title or "",
                    description=ocr_result.text,
                    category=input_data.category
                )
                result.text_moderation_result = text_result

                # Check text moderation result
                if text_result.get('decision') == 'block':
                    violations.append(ImageViolationType.TEXT_VIOLATION)
                    violation_scores['text_violation'] = text_result.get('confidence', 0.9)
                    rationale.append(f"Text content violation: {text_result.get('explanation', 'Harmful text detected')}")

                elif text_result.get('decision') == 'review':
                    violations.append(ImageViolationType.TEXT_VIOLATION)
                    violation_scores['text_violation'] = text_result.get('confidence', 0.5)
                    rationale.append(f"Text requires review: {text_result.get('explanation', 'Suspicious text')}")

            except Exception as e:
                print(f"      ⚠ Text moderation error: {e}")
        else:
            print("  [3/7] No text found, skipping text moderation")

        # =========================================================
        # STEP 4: NSFW Detection
        # =========================================================
        print("  [4/7] Running NSFW detection...")
        nsfw_result = self.nsfw_analyzer.analyze(image_path)
        result.nsfw_scores = {
            'nudity': nsfw_result.get('nudity_score', 0),
            'explicit': nsfw_result.get('explicit_score', 0),
            'safe': nsfw_result.get('safe_score', 1)
        }
        analyses.append("nsfw_detection")

        if nsfw_result.get('is_nsfw'):
            if nsfw_result.get('violation'):
                violations.append(nsfw_result['violation'])
            violation_scores['nsfw'] = nsfw_result.get('nudity_score', 0)
            rationale.append(f"NSFW content detected (score: {nsfw_result.get('nudity_score', 0):.2f})")
            models_used.extend(['NudeNet', 'OpenNSFW2'])

        # =========================================================
        # STEP 5: Object Detection
        # =========================================================
        print("  [5/7] Running object detection...")
        object_result = self.object_detector.detect(image_path)
        result.objects_detected = object_result.get('objects', [])
        result.weapon_detected = object_result.get('weapon_detected', False)
        result.weapon_score = object_result.get('weapon_score', 0)
        analyses.append("object_detection")

        if result.weapon_detected:
            violations.append(ImageViolationType.WEAPONS)
            violation_scores['weapons'] = result.weapon_score
            weapon_types = object_result.get('weapon_types', [])
            rationale.append(f"Weapons detected: {', '.join(weapon_types[:3])}")
            models_used.append('YOLOv8')

        # =========================================================
        # STEP 6: Scene Analysis
        # =========================================================
        print("  [6/7] Analyzing scene context...")
        scene_result = self.scene_analyzer.analyze(image_path)
        result.scene_classification = SceneClassification(
            scene_type=scene_result.get('scene_type', 'unknown'),
            confidence=scene_result.get('scene_confidence', 0),
            attributes=scene_result.get('attributes', [])
        )
        analyses.append("scene_analysis")

        if scene_result.get('concerning'):
            rationale.extend(scene_result.get('concerning_reasons', [])[:2])
            models_used.append('ViT')

        # =========================================================
        # STEP 7: Violence Detection
        # =========================================================
        print("  [7/7] Checking for violence/gore...")
        violence_result = self.violence_detector.analyze(image_path)
        result.violence_detected = violence_result.get('violence_detected', False)
        result.violence_score = violence_result.get('violence_score', 0)
        analyses.append("violence_detection")

        if violence_result.get('gore_detected'):
            violations.append(ImageViolationType.GORE)
            violation_scores['gore'] = violence_result.get('gore_score', 0)
            rationale.append(f"Gore content detected")

        elif violence_result.get('violence_detected'):
            violations.append(ImageViolationType.VIOLENCE)
            violation_scores['violence'] = result.violence_score
            rationale.append(f"Violence detected (score: {result.violence_score:.2f})")

        # =========================================================
        # STEP 8: Aggregate and Make Decision
        # =========================================================
        result.violations = list(set(violations))
        result.violation_scores = violation_scores
        result.detailed_rationale = rationale
        result.models_used = list(set(models_used))
        result.analyses_performed = analyses

        decision, confidence = self._make_decision(result)
        result.decision = decision
        result.confidence = confidence

        # =========================================================
        # STEP 9: Generate Explanation
        # =========================================================
        result.explanation = self._generate_explanation(result)

        # Calculate processing time
        result.processing_time_ms = (time.time() - start_time) * 1000

        print(f"\n  Decision: {result.decision.value.upper()} (confidence: {result.confidence:.2f})")

        return result

    def _make_decision(
        self,
        result: ImageModerationResult
    ) -> tuple[ImageModerationDecision, float]:
        """
        Make final moderation decision based on all analysis.

        Returns:
            Tuple of (decision, confidence)
        """
        # Auto-block conditions
        if ImageViolationType.MALICIOUS_DATA in result.violations:
            return ImageModerationDecision.BLOCK, 0.99

        if ImageViolationType.GORE in result.violations:
            return ImageModerationDecision.BLOCK, 0.95

        # NSFW check
        nsfw_score = max(
            result.nsfw_scores.get('nudity', 0),
            result.nsfw_scores.get('explicit', 0)
        )
        if nsfw_score >= self.NSFW_BLOCK_THRESHOLD:
            return ImageModerationDecision.BLOCK, 0.9

        # Weapon check
        if result.weapon_detected and result.weapon_score >= self.WEAPON_BLOCK_THRESHOLD:
            return ImageModerationDecision.BLOCK, 0.9

        # Violence check
        if result.violence_detected and result.violence_score >= self.VIOLENCE_BLOCK_THRESHOLD:
            return ImageModerationDecision.BLOCK, 0.85

        # Text violation from OCR
        if result.text_moderation_result:
            if result.text_moderation_result.get('decision') == 'block':
                return ImageModerationDecision.BLOCK, 0.85

        # Review conditions
        if nsfw_score >= self.NSFW_REVIEW_THRESHOLD:
            return ImageModerationDecision.REVIEW, 0.7

        if result.weapon_detected and result.weapon_score >= self.WEAPON_REVIEW_THRESHOLD:
            return ImageModerationDecision.REVIEW, 0.7

        if result.violence_detected and result.violence_score >= self.VIOLENCE_REVIEW_THRESHOLD:
            return ImageModerationDecision.REVIEW, 0.7

        if result.text_moderation_result:
            if result.text_moderation_result.get('decision') == 'review':
                return ImageModerationDecision.REVIEW, 0.65

        # Any other violations
        if result.violations:
            return ImageModerationDecision.REVIEW, 0.6

        # Approve if no issues
        confidence = 1.0 - max(
            nsfw_score * 0.5,
            result.weapon_score * 0.5,
            result.violence_score * 0.3
        )
        return ImageModerationDecision.APPROVE, min(confidence, 0.95)

    def _generate_explanation(self, result: ImageModerationResult) -> str:
        """Generate human-readable explanation"""
        if result.decision == ImageModerationDecision.APPROVE:
            return "Image approved. No policy violations detected."

        if result.decision == ImageModerationDecision.BLOCK:
            reasons = result.detailed_rationale[:3] if result.detailed_rationale else ["Policy violation"]
            return f"Image blocked. {' | '.join(reasons)}"

        # Review
        reasons = result.detailed_rationale[:3] if result.detailed_rationale else ["Requires manual review"]
        return f"Image flagged for review. {' | '.join(reasons)}"

    def moderate_simple(
        self,
        image_path: str,
        ad_title: str = None,
        ad_description: str = None,
        category: str = None
    ) -> ImageModerationResult:
        """
        Convenience method for simple image moderation.

        Args:
            image_path: Path to image file
            ad_title: Optional ad title for context
            ad_description: Optional ad description for context
            category: Optional category for context

        Returns:
            ImageModerationResult
        """
        input_data = ImageModerationInput(
            image_path=image_path,
            ad_title=ad_title,
            ad_description=ad_description,
            category=category
        )
        return self.moderate(input_data)


# Singleton instance
_pipeline_instance: Optional[ImageModerationPipeline] = None


def get_image_moderator() -> ImageModerationPipeline:
    """Get or create the image moderation pipeline singleton"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = ImageModerationPipeline()
    return _pipeline_instance


def moderate_image(
    image_path: str,
    ad_title: str = None,
    ad_description: str = None,
    category: str = None
) -> Dict[str, Any]:
    """
    Quick function to moderate an image.

    Args:
        image_path: Path to image file
        ad_title: Optional ad title
        ad_description: Optional ad description
        category: Optional category

    Returns:
        Dict with moderation results
    """
    pipeline = get_image_moderator()
    result = pipeline.moderate_simple(image_path, ad_title, ad_description, category)

    return {
        'decision': result.decision.value,
        'confidence': result.confidence,
        'violations': [v.value for v in result.violations],
        'explanation': result.explanation,
        'nsfw_scores': result.nsfw_scores,
        'weapon_detected': result.weapon_detected,
        'weapon_score': result.weapon_score,
        'violence_detected': result.violence_detected,
        'violence_score': result.violence_score,
        'has_text': result.ocr_result.has_text if result.ocr_result else False,
        'extracted_text': result.ocr_result.text if result.ocr_result else "",
        'text_moderation': result.text_moderation_result,
        'processing_time_ms': result.processing_time_ms
    }


if __name__ == "__main__":
    import sys

    print("\n" + "="*70)
    print("  IMAGE MODERATION PIPELINE TEST")
    print("="*70 + "\n")

    if len(sys.argv) > 1:
        image_path = sys.argv[1]

        if os.path.exists(image_path):
            result = moderate_image(image_path)

            print(f"\n📋 Decision: {result['decision'].upper()}")
            print(f"🎯 Confidence: {result['confidence']:.2%}")

            if result['violations']:
                print(f"⚠️ Violations: {', '.join(result['violations'])}")

            print(f"\n💬 {result['explanation']}")
            print(f"⏱️ Processing time: {result['processing_time_ms']:.1f}ms")
        else:
            print(f"❌ File not found: {image_path}")
    else:
        print("Usage: python pipeline.py <image_path>")

