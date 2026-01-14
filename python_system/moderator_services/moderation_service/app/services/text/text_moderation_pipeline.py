"""
Text Moderation Pipeline (Backward Compatibility)
=================================================

This file maintains backward compatibility by re-exporting
from the new modular structure.

The pipeline has been refactored into smaller modules:
- models.py      - Data classes and enums
- normalizer.py  - Text normalization and tokenization
- language.py    - Language detection
- embeddings.py  - Semantic encoder and vector database
- classifiers.py - Intent and context classifiers
- aggregator.py  - Feature aggregation
- policy.py      - Policy evaluation
- utils.py       - Explanation generator and keyword matcher
- pipeline.py    - Main pipeline orchestrator
"""

# Re-export everything for backward compatibility
from .models import (
    ModerationDecision,
    ViolationType,
    TextModerationInput,
    TextModerationResult
)

from .normalizer import TextNormalizer
from .language import LanguageDetector
from .embeddings import SemanticEncoder, VectorDatabase
from .classifiers import IntentClassifier, ContextClassifier
from .aggregator import FeatureAggregator
from .policy import PolicyEvaluator
from .utils import ExplanationGenerator, KeywordMatcher

from .pipeline import (
    TextModerationPipeline,
    get_text_moderator,
    moderate_text
)

__all__ = [
    'ModerationDecision',
    'ViolationType',
    'TextModerationInput',
    'TextModerationResult',
    'TextNormalizer',
    'LanguageDetector',
    'SemanticEncoder',
    'VectorDatabase',
    'IntentClassifier',
    'ContextClassifier',
    'FeatureAggregator',
    'PolicyEvaluator',
    'ExplanationGenerator',
    'KeywordMatcher',
    'TextModerationPipeline',
    'get_text_moderator',
    'moderate_text'
]

