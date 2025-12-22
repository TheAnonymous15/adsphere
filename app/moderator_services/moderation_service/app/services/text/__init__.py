"""
Text Moderation Services
========================

Comprehensive text moderation pipeline with:
- Language detection (fastText)
- Semantic encoding (Sentence Transformers)
- Intent classification (DeBERTa/BART)
- Toxicity detection (Detoxify)
- Policy evaluation
"""

from .text_moderation_pipeline import (
    TextModerationPipeline,
    TextModerationInput,
    TextModerationResult,
    ModerationDecision,
    ViolationType,
    get_text_moderator,
    moderate_text
)

__all__ = [
    'TextModerationPipeline',
    'TextModerationInput',
    'TextModerationResult',
    'ModerationDecision',
    'ViolationType',
    'get_text_moderator',
    'moderate_text'
]

