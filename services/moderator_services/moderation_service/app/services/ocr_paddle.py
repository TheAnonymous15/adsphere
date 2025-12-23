"""
OCR service using PaddleOCR
Extracts text from images and video frames
"""
import sys
from pathlib import Path
from typing import List, Dict
import os

# Set up paths for model_registry import
# Path: services/ocr_paddle.py -> services -> app -> moderation_service -> moderator_services
CURRENT_DIR = Path(__file__).parent.resolve()
APP_DIR = CURRENT_DIR.parent.resolve()
MODERATION_SERVICE_DIR = APP_DIR.parent.resolve()
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent.resolve()

for _path in [str(MODERATOR_SERVICES_DIR), str(MODERATION_SERVICE_DIR), str(APP_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from model_registry import ensure_models

# Ensure required models are available
REQUIRED_MODELS = ['paddleocr']
if not ensure_models(REQUIRED_MODELS, verbose=False):
    print("⚠ OCRService: PaddleOCR not available")


class OCRService:
    """
    PaddleOCR-based text extraction.

    Extracts text from images to detect:
    - Phishing URLs
    - Illegal offers
    - Scam text
    - Contact information (for spam detection)
    """

    def __init__(self, lang: str = 'en'):
        """
        Initialize OCR engine.

        Args:
            lang: Language code ('en', 'ch', 'french', etc.)
        """
        self.ocr = None
        self.lang = lang
        self._load_model()

    def _load_model(self):
        """Lazy load PaddleOCR"""
        try:
            import os
            from paddleocr import PaddleOCR
            import logging

            # Disable slow model source check to speed up initialization
            os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

            # Suppress PaddleOCR logging
            logging.getLogger('ppocr').setLevel(logging.WARNING)

            # Initialize PaddleOCR with minimal parameters
            # Note: Parameters vary by PaddleOCR version
            self.ocr = PaddleOCR(lang=self.lang)
            print(f"✓ PaddleOCR loaded (lang={self.lang})")
        except Exception as e:
            print(f"⚠ PaddleOCR not available: {e}")
            self.ocr = None

    def extract_text(self, image_path: str, confidence_threshold: float = 0.5) -> Dict[str, any]:
        """
        Extract text from image.

        Args:
            image_path: Path to image file
            confidence_threshold: Minimum confidence for text detection

        Returns:
            Dict with extracted text and metadata
        """
        if self.ocr is None:
            return {
                "text": "",
                "lines": [],
                "error": "OCR not initialized"
            }

        if not os.path.exists(image_path):
            return {
                "text": "",
                "lines": [],
                "error": "Image not found"
            }

        try:
            result = self.ocr.ocr(image_path, cls=True)

            if not result or not result[0]:
                return {
                    "text": "",
                    "lines": [],
                    "num_lines": 0
                }

            lines = []
            full_text = []

            for line in result[0]:
                if not line:
                    continue

                # PaddleOCR returns: [bbox, (text, confidence)]
                bbox, (text, conf) = line

                if conf >= confidence_threshold:
                    lines.append({
                        "text": text,
                        "confidence": float(conf),
                        "bbox": bbox
                    })
                    full_text.append(text)

            combined_text = "\n".join(full_text)

            return {
                "text": combined_text,
                "lines": lines,
                "num_lines": len(lines)
            }

        except Exception as e:
            print(f"OCR error on {image_path}: {e}")
            return {
                "text": "",
                "lines": [],
                "error": str(e)
            }

    def extract_from_frames(self, frame_paths: List[str]) -> Dict[str, any]:
        """
        Extract text from multiple video frames.

        Args:
            frame_paths: List of frame image paths

        Returns:
            Aggregated OCR results
        """
        all_text = []
        all_lines = []
        frames_with_text = 0

        for frame_path in frame_paths:
            result = self.extract_text(frame_path)

            text = result.get("text", "")
            if text.strip():
                frames_with_text += 1
                all_text.append(text)
                all_lines.extend(result.get("lines", []))

        combined_text = "\n\n".join(all_text)

        return {
            "text": combined_text,
            "all_lines": all_lines,
            "frames_with_text": frames_with_text,
            "total_frames": len(frame_paths),
            "num_text_lines": len(all_lines)
        }

    def detect_urls(self, text: str) -> List[str]:
        """
        Detect URLs in extracted text (for phishing detection).

        Args:
            text: Extracted text

        Returns:
            List of detected URLs
        """
        import re
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
        urls = re.findall(url_pattern, text)
        return urls

    def detect_phone_numbers(self, text: str) -> List[str]:
        """
        Detect phone numbers in text.

        Args:
            text: Extracted text

        Returns:
            List of detected phone numbers
        """
        import re
        # Match various phone number formats
        phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        phones = re.findall(phone_pattern, text)
        return phones

