"""
Text Moderation Services
========================

Provides backward-compatible namespace for the text moderation
pipeline and individual components following modular refactor.
"""

import sys
from pathlib import Path

# Set up paths for model_registry import
# Path: text/__init__.py -> text -> services -> app -> moderation_service -> moderator_services
TEXT_DIR = Path(__file__).parent.resolve()
SERVICES_DIR = TEXT_DIR.parent.resolve()
APP_DIR = SERVICES_DIR.parent.resolve()
MODERATION_SERVICE_DIR = APP_DIR.parent.resolve()
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent.resolve()

for _path in [str(MODERATOR_SERVICES_DIR), str(MODERATION_SERVICE_DIR), str(APP_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

__version__ = "2.0.0"
__compat__ = "1.x legacy API maintained"

import warnings

warnings.warn(
    "Importing from the package root is deprecated; use modular imports.",
    DeprecationWarning,
    stacklevel=2
)

# Models
from .models import (
    ModerationDecision,
    ViolationType,
    TextModerationInput,
    TextModerationResult
)

# Pipeline entrypoints
from .pipeline import (
    TextModerationPipeline,
    get_text_moderator as _get_text_moderator,
    moderate_text
)

def get_text_moderator(*args, **kwargs):
    """Backward compatible entrypoint wrapper."""
    return _get_text_moderator(*args, **kwargs)

# Lightweight components imported statically
from .normalizer import TextNormalizer
from .language import LanguageDetector
from .utils import ExplanationGenerator, KeywordMatcher
from .aggregator import FeatureAggregator
from .policy import PolicyEvaluator

# Heavy components lazily imported on access
def __getattr__(name):
    if name in ("SemanticEncoder", "VectorDatabase"):
        from .embeddings import SemanticEncoder, VectorDatabase
        return {"SemanticEncoder": SemanticEncoder, "VectorDatabase": VectorDatabase}[name]

    if name in ("IntentClassifier", "ContextClassifier"):
        from .classifiers import IntentClassifier, ContextClassifier
        return {"IntentClassifier": IntentClassifier, "ContextClassifier": ContextClassifier}[name]

    raise AttributeError(f"module does not export {name!r}")


__all__ = [
    # Pipeline
    'TextModerationPipeline',
    'get_text_moderator',
    'moderate_text',

    # Models
    'TextModerationInput',
    'TextModerationResult',
    'ModerationDecision',
    'ViolationType',

    # Lightweight static component exports
    'TextNormalizer',
    'LanguageDetector',
    'ExplanationGenerator',
    'KeywordMatcher',
    'PolicyEvaluator',
    'FeatureAggregator',

    # Lazy heavy components
    'SemanticEncoder',
    'VectorDatabase',
    'IntentClassifier',
    'ContextClassifier'
]
