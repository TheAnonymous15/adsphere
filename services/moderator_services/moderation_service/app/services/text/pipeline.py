"""
Text Moderation Pipeline
========================

Main orchestrator that coordinates all 10 steps of text analysis.
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent))

try:
    from model_registry import ensure_models
except ImportError:
    def ensure_models(models, verbose=False):
        return True

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


class TextModerationPipeline:
    """
    Complete text moderation pipeline.
    Orchestrates all 10 steps of text analysis.
    """

    def __init__(self, preload_models: bool = True):
        """Initialize the pipeline"""
        print("\n" + "="*60)
        print("  Initializing Text Moderation Pipeline")
        print("="*60 + "\n")

        # Ensure required models
        required_models = ['transformers', 'torch']
        ensure_models(required_models, verbose=False)

        # Initialize components
        self.normalizer = TextNormalizer()
        self.language_detector = LanguageDetector()
        self.semantic_encoder = SemanticEncoder()
        self.vector_db = VectorDatabase(encoder=self.semantic_encoder)
        self.intent_classifier = IntentClassifier()
        self.context_classifier = ContextClassifier()
        self.feature_aggregator = FeatureAggregator()
        self.policy_evaluator = PolicyEvaluator()
        self.explanation_generator = ExplanationGenerator()
        self.keyword_matcher = KeywordMatcher()

        print("\n" + "="*60)
        print("  Text Moderation Pipeline Ready")
        print("="*60 + "\n")


    def moderate(self, input_data: TextModerationInput) -> TextModerationResult:
        """
        Run complete moderation pipeline on input.

        Args:
            input_data: TextModerationInput with title and description

        Returns:
            TextModerationResult with decision and analysis
        """
        start_time = time.time()
        models_used = []

        # Combine title and description
        full_text = f"{input_data.title} {input_data.description}".strip()

        if not full_text:
            return TextModerationResult(
                decision=ModerationDecision.APPROVE,
                confidence=1.0,
                explanation="Empty content - auto-approved",
                processing_time_ms=0
            )

        # Step 2: Normalize text
        normalized_text = self.normalizer.normalize(full_text)
        tokens = self.normalizer.tokenize(full_text)
        entities = self.normalizer.extract_entities(full_text)

        # Step 3: Detect language
        detected_lang, lang_confidence = self.language_detector.detect(full_text)
        if self.language_detector.classifier:
            models_used.append("XLM-RoBERTa-LID")

        # Step 4: Semantic encoding
        embedding = self.semantic_encoder.encode(normalized_text)
        if embedding:
            models_used.append("SentenceTransformer")

        # Step 5: Vector similarity search
        similar_violations = []
        if embedding:
            similar_violations = self.vector_db.search(embedding, k=5)
            if similar_violations:
                models_used.append("FAISS")

        # Step 6: Intent classification
        intent, intent_conf, intent_scores = self.intent_classifier.classify(full_text)
        if self.intent_classifier.classifier:
            models_used.append("BART-MNLI")

        # Step 7: Context/toxicity classification
        toxicity_scores = self.context_classifier.classify(full_text)
        if self.context_classifier.model:
            models_used.append("Polyglot-Toxic")
        elif hasattr(self.context_classifier, '_detoxify') and self.context_classifier._detoxify:
            models_used.append("Detoxify")

        # Keyword matching
        matched_keywords, keyword_violations = self.keyword_matcher.match(full_text)

        # Step 8: Feature aggregation
        risk_score, violations, component_scores = self.feature_aggregator.aggregate(
            toxicity_scores=toxicity_scores,
            intent_scores=intent_scores,
            semantic_matches=similar_violations,
            keyword_flags=matched_keywords,
            context_flags=[]
        )

        # Add keyword violations
        violations.extend(keyword_violations)
        violations = list(set(violations))

        # Step 9: Policy evaluation
        decision, confidence, policy_violations = self.policy_evaluator.evaluate(
            risk_score=risk_score,
            violations=violations,
            toxicity_scores=toxicity_scores,
            category=input_data.category,
            price=input_data.price
        )

        # Step 10: Generate explanation
        explanation, rationale = self.explanation_generator.generate(
            decision=decision,
            violations=violations,
            policy_violations=policy_violations,
            component_scores=component_scores,
            detected_language=detected_lang
        )

        # Build result
        processing_time = (time.time() - start_time) * 1000

        violation_scores = {}
        for v in violations:
            violation_scores[v.value] = component_scores.get(v.value, risk_score)

        return TextModerationResult(
            decision=decision,
            confidence=confidence,
            violations=violations,
            violation_scores=violation_scores,
            detected_language=detected_lang,
            language_confidence=lang_confidence,
            detected_intent=intent,
            intent_confidence=intent_conf,
            toxicity_scores=toxicity_scores,
            semantic_flags=[m.get('text', '') for m in similar_violations if m.get('similarity', 0) > 0.5],
            similar_violations=similar_violations,
            policy_violations=policy_violations,
            policy_score=1.0 - risk_score,
            explanation=explanation,
            detailed_rationale=rationale,
            processing_time_ms=processing_time,
            models_used=models_used
        )

    def moderate_simple(self, title: str, description: str,
                        category: str = None) -> TextModerationResult:
        """Convenience method for simple moderation"""
        input_data = TextModerationInput(
            title=title,
            description=description,
            category=category
        )
        return self.moderate(input_data)


# Singleton instance
_pipeline_instance: Optional[TextModerationPipeline] = None


def get_text_moderator() -> TextModerationPipeline:
    """Get or create the text moderation pipeline singleton"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = TextModerationPipeline()
    return _pipeline_instance


def moderate_text(title: str, description: str, category: str = None) -> Dict[str, Any]:
    """
    Quick function to moderate text.

    Returns dict with:
        - decision: "approve", "review", or "block"
        - confidence: 0.0 to 1.0
        - violations: list of violation types
        - explanation: human-readable explanation
    """
    pipeline = get_text_moderator()
    result = pipeline.moderate_simple(title, description, category)

    return {
        'decision': result.decision.value,
        'confidence': result.confidence,
        'violations': [v.value for v in result.violations],
        'explanation': result.explanation,
        'toxicity_scores': result.toxicity_scores,
        'detected_language': result.detected_language,
        'processing_time_ms': result.processing_time_ms
    }

