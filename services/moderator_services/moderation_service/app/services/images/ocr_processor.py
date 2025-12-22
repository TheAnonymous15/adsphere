"""
OCR Processor
=============

Step 2: Extract text from images using OCR.
Extracted text is then passed to text moderation.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent))

try:
    from model_registry import ensure_models
except ImportError:
    def ensure_models(models, verbose=False):
        return True

from .models import OCRResult


class ImageOCRProcessor:
    """
    OCR text extraction from images.

    Uses PaddleOCR for multi-language text detection.
    Supports:
    - Multi-language text detection
    - Rotated text
    - Scene text
    - Document text
    """

    # Model registry ID
    MODEL_REGISTRY_ID = 'paddleocr'
    REQUIRED_MODELS = ['paddleocr']

    def __init__(self, languages: List[str] = None):
        """
        Initialize OCR processor.

        Args:
            languages: List of language codes to detect ['en', 'ch', 'fr', etc.]
        """
        self.languages = languages or ['en']
        self.ocr_engines = {}
        self._load_models()

    def _load_models(self):
        """Load OCR engines"""
        # Ensure model is available via registry
        if not ensure_models([self.MODEL_REGISTRY_ID], verbose=False):
            print(f"⚠ OCR model {self.MODEL_REGISTRY_ID} not available via registry")

        try:
            import os
            os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

            from paddleocr import PaddleOCR
            import logging
            logging.getLogger('ppocr').setLevel(logging.WARNING)

            # Load OCR for each language
            for lang in self.languages:
                try:
                    # Note: show_log parameter removed as it's not supported in newer PaddleOCR
                    self.ocr_engines[lang] = PaddleOCR(lang=lang)
                    print(f"✓ PaddleOCR loaded for language: {lang}")
                except Exception as e:
                    print(f"⚠ Failed to load OCR for {lang}: {e}")

        except ImportError as e:
            print(f"⚠ PaddleOCR not available: {e}")
        except Exception as e:
            print(f"⚠ OCR initialization error: {e}")

    def extract_text(
        self,
        image_path: str,
        language: str = 'en',
        confidence_threshold: float = 0.5
    ) -> OCRResult:
        """
        Extract text from image.

        Args:
            image_path: Path to image file
            language: Language code for OCR
            confidence_threshold: Minimum confidence for text detection

        Returns:
            OCRResult with extracted text
        """
        result = OCRResult()

        if not os.path.exists(image_path):
            return result

        # Get appropriate OCR engine
        ocr = self.ocr_engines.get(language) or self.ocr_engines.get('en')
        if not ocr:
            return result

        try:
            # Run OCR - the new PaddleOCR uses .ocr() method
            ocr_result = ocr.ocr(image_path)

            if not ocr_result:
                return result

            lines = []
            full_text = []
            total_confidence = 0

            # New PaddleOCR format returns a list of dicts
            # Each dict has: 'rec_texts', 'rec_scores', 'dt_polys', etc.
            if isinstance(ocr_result, list) and len(ocr_result) > 0:
                first_result = ocr_result[0]

                # Check for new format with 'rec_texts' key
                if isinstance(first_result, dict) and 'rec_texts' in first_result:
                    texts = first_result.get('rec_texts', [])
                    scores = first_result.get('rec_scores', [])

                    for i, text in enumerate(texts):
                        score = float(scores[i]) if i < len(scores) else 0.5
                        if score >= confidence_threshold:
                            lines.append({
                                'text': text,
                                'confidence': score,
                                'bbox': None
                            })
                            full_text.append(text)
                            total_confidence += score

                # Old format: list of [bbox, (text, confidence)]
                elif isinstance(first_result, list):
                    for line in first_result:
                        if not line or len(line) < 2:
                            continue

                        bbox = line[0]
                        text_info = line[1]

                        if isinstance(text_info, tuple) and len(text_info) >= 2:
                            text = text_info[0]
                            confidence = float(text_info[1])
                        elif isinstance(text_info, str):
                            text = text_info
                            confidence = 0.5
                        else:
                            continue

                        if confidence >= confidence_threshold:
                            lines.append({
                                'text': text,
                                'confidence': confidence,
                                'bbox': bbox
                            })
                            full_text.append(text)
                            total_confidence += confidence

            if lines:
                result.text = ' '.join(full_text)
                result.lines = lines
                result.num_lines = len(lines)
                result.confidence = total_confidence / len(lines)
                result.has_text = True
                result.language = language

        except Exception as e:
            print(f"⚠ OCR extraction error: {e}")

        return result

    def extract_text_all_languages(
        self,
        image_path: str,
        confidence_threshold: float = 0.5
    ) -> OCRResult:
        """
        Try OCR with all available languages and return best result.

        Args:
            image_path: Path to image file
            confidence_threshold: Minimum confidence

        Returns:
            Best OCRResult across languages
        """
        best_result = OCRResult()
        best_confidence = 0

        for lang in self.ocr_engines.keys():
            result = self.extract_text(image_path, lang, confidence_threshold)
            if result.confidence > best_confidence:
                best_result = result
                best_confidence = result.confidence

        return best_result

    def detect_text_regions(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Detect text regions without full recognition.
        Useful for quick check if image contains text.

        Args:
            image_path: Path to image file

        Returns:
            List of detected text regions with bounding boxes
        """
        regions = []

        ocr = self.ocr_engines.get('en')
        if not ocr:
            return regions

        try:
            # Detection only mode
            result = ocr.ocr(image_path, rec=False)

            if result and result[0]:
                for bbox in result[0]:
                    regions.append({
                        'bbox': bbox,
                        'area': self._calculate_bbox_area(bbox)
                    })

        except Exception as e:
            print(f"⚠ Text detection error: {e}")

        return regions

    def _calculate_bbox_area(self, bbox: List) -> float:
        """Calculate bounding box area"""
        try:
            if len(bbox) >= 4:
                width = abs(bbox[1][0] - bbox[0][0])
                height = abs(bbox[2][1] - bbox[1][1])
                return width * height
        except:
            pass
        return 0

    def has_significant_text(
        self,
        image_path: str,
        min_text_length: int = 5,
        min_confidence: float = 0.6
    ) -> bool:
        """
        Quick check if image has significant text content.

        Args:
            image_path: Path to image
            min_text_length: Minimum text length to consider significant
            min_confidence: Minimum confidence threshold

        Returns:
            True if significant text detected
        """
        result = self.extract_text(image_path, confidence_threshold=min_confidence)
        return len(result.text.strip()) >= min_text_length

