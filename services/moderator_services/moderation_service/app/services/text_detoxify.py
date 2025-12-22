"""
Text toxicity detection using Detoxify
"""
import sys
from pathlib import Path
from typing import Dict

# Add parent path for model_registry import
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
from model_registry import ensure_models

# Ensure required models are available
REQUIRED_MODELS = ['detoxify', 'torch']
if not ensure_models(REQUIRED_MODELS, verbose=False):
    raise RuntimeError(f"DetoxifyService: Required models not available: {REQUIRED_MODELS}")

from detoxify import Detoxify


class DetoxifyService:
    """
    Detoxify-based text moderation.

    Detects:
    - Toxicity
    - Severe toxicity
    - Obscene language
    - Threats
    - Insults
    - Identity-based hate
    """

    def __init__(self, model_type: str = "original"):
        """
        Initialize Detoxify model.

        Args:
            model_type: 'original', 'unbiased', or 'multilingual'
        """
        self.model = Detoxify(model_type)
        self.model_type = model_type

    def analyze(self, text: str) -> Dict[str, float]:
        """
        Analyze text for toxicity.

        Args:
            text: Input text

        Returns:
            Dict with scores for each category (0.0-1.0)
        """
        if not text or not text.strip():
            return {
                'toxicity': 0.0,
                'severe_toxicity': 0.0,
                'obscene': 0.0,
                'threat': 0.0,
                'insult': 0.0,
                'identity_attack': 0.0
            }

        # Truncate very long text
        text = text[:5000]

        try:
            scores = self.model.predict(text)

            # Convert numpy float32 to Python float
            result = {k: float(v) for k, v in scores.items()}
            return result

        except Exception as e:
            print(f"Error in Detoxify analysis: {e}")
            return {
                'toxicity': 0.0,
                'severe_toxicity': 0.0,
                'obscene': 0.0,
                'threat': 0.0,
                'insult': 0.0,
                'identity_attack': 0.0
            }

