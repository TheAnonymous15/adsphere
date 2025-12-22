"""
Classifiers Module
==================

Step 6 & 7: Intent and context classification.

Models are loaded through the model_registry for centralized management.
"""

import sys
from pathlib import Path
from typing import Dict, Tuple

# Add parent paths for model_registry imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent))

try:
    from model_registry import ensure_models, get_model_path, ModelStore
except ImportError:
    # Fallback if model_registry not found
    def ensure_models(models, verbose=False):
        return True
    def get_model_path(model_id):
        return None
    ModelStore = None


class IntentClassifier:
    """
    Step 6: Intent classification using transformer models.

    Uses BART-MNLI for zero-shot classification of ad intent.
    Model loaded via model_registry.
    """

    # Intent categories for ads - specific to distinguish actual violations from legitimate content
    INTENTS = [
        "legitimate_product_or_service",  # Normal product/service ad
        "educational_or_informational",   # News, education, discussion
        "spam_or_clickbait",              # Spam or low-quality content
        "financial_scam",                 # Money scams, get-rich-quick
        "illegal_goods_for_sale",         # Actually selling illegal items
        "sexual_services_for_sale",       # Actually selling sexual services
        "hate_or_discrimination",         # Hate or discriminatory content
        "violence_or_threat",             # Actual threats of violence
        "personal_attack",                # Targeted harassment
        "false_claims",                   # Misleading health/product claims
    ]

    # Required models for this classifier
    REQUIRED_MODELS = ['transformers', 'torch']

    # Model registry ID
    MODEL_REGISTRY_ID = 'bart_mnli'

    # HuggingFace model name (loaded via model_registry preload)
    MODEL_NAME = "facebook/bart-large-mnli"

    def __init__(self):
        self.classifier = None
        self._load_model()

    def _load_model(self):
        """Load intent classification model via model_registry"""
        # Ensure required base models are available
        if not ensure_models(self.REQUIRED_MODELS, verbose=False):
            print("⚠ Required models for IntentClassifier not available")
            return

        # Ensure the bart_mnli model is downloaded via registry
        if not ensure_models([self.MODEL_REGISTRY_ID], verbose=False):
            print(f"⚠ Model {self.MODEL_REGISTRY_ID} not available via registry, trying direct load")

        try:
            from transformers import pipeline

            # Use zero-shot classification (model already downloaded by registry)
            self.classifier = pipeline(
                "zero-shot-classification",
                model=self.MODEL_NAME,
                device=-1  # CPU
            )
            print(f"✓ Intent classifier loaded ({self.MODEL_NAME})")
        except Exception as e:
            print(f"⚠ Intent classifier not available: {e}")

    def classify(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        """Classify intent of text"""
        if not self.classifier or not text:
            return "legitimate_product_or_service", 0.5, {}

        try:
            result = self.classifier(
                text,
                candidate_labels=self.INTENTS,
                multi_label=False
            )

            top_intent = result['labels'][0]
            top_score = result['scores'][0]

            scores = dict(zip(result['labels'], result['scores']))

            return top_intent, top_score, scores

        except Exception as e:
            print(f"⚠ Intent classification error: {e}")
            return "legitimate_product_or_service", 0.5, {}


class ContextClassifier:
    """
    Step 7: Multilingual contextual toxicity classification.

    Uses citizenlab/distilbert-base-multilingual-cased-toxicity for multilingual toxicity detection.
    Model loaded via model_registry.

    Fallback to Detoxify if primary model unavailable.
    """

    LABELS = [
        "toxicity",
        "severe_toxicity",
        "obscene",
        "threat",
        "insult",
        "identity_attack"
    ]

    # Required models for this classifier
    REQUIRED_MODELS = ['transformers', 'torch']

    # Model registry ID for the toxicity model
    MODEL_REGISTRY_ID = 'polyglot_toxic'

    # HuggingFace model name (loaded via model_registry preload)
    MODEL_NAME = "citizenlab/distilbert-base-multilingual-cased-toxicity"

    def __init__(self, threshold: float = 0.5, device: str = None):
        self.threshold = threshold
        self.device = device
        self.model = None
        self.tokenizer = None
        self._detoxify = None
        self._load_model()

    def _load_model(self):
        """Load toxicity classification model via model_registry"""
        # Ensure required base models are available
        if not ensure_models(self.REQUIRED_MODELS, verbose=False):
            print("⚠ Required models for ContextClassifier not available")
            self._try_fallback()
            return

        # Ensure the polyglot_toxic model is downloaded via registry
        if not ensure_models([self.MODEL_REGISTRY_ID], verbose=False):
            print(f"⚠ Model {self.MODEL_REGISTRY_ID} not available via registry")
            self._try_fallback()
            return

        try:
            import torch
            from transformers import (
                AutoTokenizer,
                AutoModelForSequenceClassification
            )

            # Determine device
            if self.device is None:
                self.device = "cuda" if torch.cuda.is_available() else "cpu"

            # Load model and tokenizer (already downloaded by model_registry)
            self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.MODEL_NAME)

            self.model.to(self.device)
            self.model.eval()

            print(f"✓ Multilingual toxicity classifier loaded ({self.MODEL_NAME}, device={self.device})")
        except Exception as e:
            print(f"⚠ Toxicity classifier unavailable: {e}")
            self.model = None
            self._try_fallback()

    def _try_fallback(self):
        """Try fallback to Detoxify if Polyglot fails"""
        try:
            # Check if detoxify is available via model_registry
            if ensure_models(['detoxify'], verbose=False):
                from detoxify import Detoxify
                self._detoxify = Detoxify('original')
                print("✓ Fallback to Detoxify loaded")
            else:
                self._detoxify = None
        except Exception:
            self._detoxify = None

    def classify(self, text: str) -> Dict[str, float]:
        """Get multilingual toxicity scores for text"""
        # Fallback zero scores
        scores = {label: 0.0 for label in self.LABELS}

        if not text:
            return scores

        # Try multilingual model first
        if self.model is not None:
            return self._classify_multilingual(text)

        # Fallback to Detoxify
        if hasattr(self, '_detoxify') and self._detoxify is not None:
            return self._classify_detoxify(text)

        return scores

    def _classify_multilingual(self, text: str) -> Dict[str, float]:
        """Classify using multilingual toxicity model"""
        scores = {label: 0.0 for label in self.LABELS}

        try:
            import torch

            with torch.inference_mode():
                encoded = self.tokenizer(
                    text[:2000],
                    truncation=True,
                    max_length=256,
                    padding=True,
                    return_tensors="pt"
                ).to(self.device)

                logits = self.model(**encoded).logits
                probs = torch.sigmoid(logits).cpu().numpy()[0]

                for idx, label in enumerate(self.LABELS):
                    if idx < len(probs):
                        scores[label] = float(probs[idx])

        except Exception as e:
            print(f"⚠ Multilingual toxicity classification error: {e}")

        return scores

    def _classify_detoxify(self, text: str) -> Dict[str, float]:
        """Classify using Detoxify (fallback)"""
        scores = {label: 0.0 for label in self.LABELS}

        try:
            result = self._detoxify.predict(text[:5000])
            scores = {k: float(v) for k, v in result.items()}
        except Exception as e:
            print(f"⚠ Detoxify classification error: {e}")

        return scores

