"""
Language Detector
=================

Step 3: Language detection using XLM-RoBERTa.
"""

from typing import Tuple


class LanguageDetector:
    """Step 3: Language detection using XLM-RoBERTa (papluca/xlm-roberta-base-language-detection)"""

    # Language code mapping from model labels to ISO codes
    LANG_MAP = {
        'arabic': 'ar',
        'bulgarian': 'bg',
        'german': 'de',
        'modern greek': 'el',
        'english': 'en',
        'spanish': 'es',
        'french': 'fr',
        'hindi': 'hi',
        'italian': 'it',
        'japanese': 'ja',
        'dutch': 'nl',
        'polish': 'pl',
        'portuguese': 'pt',
        'russian': 'ru',
        'swahili': 'sw',
        'thai': 'th',
        'turkish': 'tr',
        'urdu': 'ur',
        'vietnamese': 'vi',
        'chinese': 'zh',
    }

    def __init__(self):
        self.classifier = None
        self._load_model()

    def _load_model(self):
        """Load XLM-RoBERTa language detection model from HuggingFace"""
        try:
            from transformers import pipeline

            self.classifier = pipeline(
                "text-classification",
                model="papluca/xlm-roberta-base-language-detection",
                device=-1,  # CPU
                top_k=1
            )
            print("✓ XLM-RoBERTa Language Detector loaded (papluca/xlm-roberta-base-language-detection)")

        except Exception as e:
            print(f"⚠ XLM-RoBERTa language detector not available: {e}")
            print("  Falling back to heuristic detection")
            self.classifier = None

    def detect(self, text: str) -> Tuple[str, float]:
        """Detect language of text"""
        if not text or len(text.strip()) < 3:
            return "en", 0.5

        if self.classifier:
            try:
                # Truncate text to avoid issues with very long inputs
                text_truncated = text[:512].replace('\n', ' ')

                result = self.classifier(text_truncated)

                # Handle different output formats
                if isinstance(result, list) and len(result) > 0:
                    if isinstance(result[0], list):
                        # top_k returns list of lists
                        top_result = result[0][0]
                    else:
                        top_result = result[0]

                    label = top_result.get('label', 'english').lower()
                    confidence = float(top_result.get('score', 0.5))

                    # Map to ISO language code
                    lang_code = self.LANG_MAP.get(label, label[:2])

                    return lang_code, confidence

            except Exception as e:
                print(f"⚠ Language detection error: {e}")

        # Fallback: simple heuristic
        return self._fallback_detect(text)

    def _fallback_detect(self, text: str) -> Tuple[str, float]:
        """Simple fallback language detection"""
        # Check for common language patterns
        text_lower = text.lower()

        # Spanish indicators
        if any(w in text_lower for w in ['está', 'está', 'qué', 'cómo', 'para']):
            return "es", 0.7

        # French indicators
        if any(w in text_lower for w in ['est', 'sont', 'avec', 'pour', 'dans']):
            return "fr", 0.7

        # German indicators
        if any(w in text_lower for w in ['ist', 'sind', 'und', 'für', 'auf']):
            return "de", 0.7

        # Swahili indicators
        if any(w in text_lower for w in ['na', 'kwa', 'ya', 'ni', 'wa']):
            return "sw", 0.7

        # Default to English
        return "en", 0.6

