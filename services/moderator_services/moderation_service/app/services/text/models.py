"""
Text Moderation Models
======================

Data classes, enums, and type definitions for text moderation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class ModerationDecision(Enum):
    """Moderation decision outcomes"""
    APPROVE = "approve"
    REVIEW = "review"
    BLOCK = "block"


class ViolationType(Enum):
    """Types of content violations"""
    NONE = "none"
    TOXICITY = "toxicity"
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    SEXUAL = "sexual"
    SPAM = "spam"
    SCAM = "scam"
    ILLEGAL = "illegal"
    WEAPONS = "weapons"
    DRUGS = "drugs"
    HARASSMENT = "harassment"
    SELF_HARM = "self_harm"
    MISLEADING = "misleading"


@dataclass
class TextModerationInput:
    """Input for text moderation"""
    title: str
    description: str
    category: Optional[str] = None
    price: Optional[float] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class TextModerationResult:
    """Complete moderation result"""
    # Decision
    decision: ModerationDecision
    confidence: float

    # Violations found
    violations: List[ViolationType] = field(default_factory=list)
    violation_scores: Dict[str, float] = field(default_factory=dict)

    # Language detection
    detected_language: str = "en"
    language_confidence: float = 1.0

    # Intent analysis
    detected_intent: str = "legitimate_ad"
    intent_confidence: float = 1.0

    # Toxicity scores
    toxicity_scores: Dict[str, float] = field(default_factory=dict)

    # Semantic analysis
    semantic_flags: List[str] = field(default_factory=list)
    similar_violations: List[Dict] = field(default_factory=list)

    # Policy
    policy_score: float = 1.0
    policy_violations: List[str] = field(default_factory=list)

    # Explanation
    explanation: str = ""
    detailed_rationale: List[str] = field(default_factory=list)

    # Processing metadata
    processing_time_ms: float = 0.0
    models_used: List[str] = field(default_factory=list)

