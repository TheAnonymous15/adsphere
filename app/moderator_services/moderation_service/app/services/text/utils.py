"""
Utility Classes
===============

Step 10: Explanation generation and keyword matching utilities.
"""

from typing import Dict, List, Tuple

from .models import ModerationDecision, ViolationType


class ExplanationGenerator:
    """Step 10: Generate decision explanation"""

    def __init__(self):
        self.templates = {
            ModerationDecision.APPROVE: "Content approved. {details}",
            ModerationDecision.REVIEW: "Content flagged for manual review. {details}",
            ModerationDecision.BLOCK: "Content blocked. {details}"
        }

    def generate(
        self,
        decision: ModerationDecision,
        violations: List[ViolationType],
        policy_violations: List[str],
        component_scores: Dict[str, float],
        detected_language: str
    ) -> Tuple[str, List[str]]:
        """
        Generate human-readable explanation for the decision.

        Returns:
            - explanation: summary explanation
            - detailed_rationale: list of specific reasons
        """
        rationale = []

        # Add violation reasons
        if violations:
            violation_names = [v.value.replace('_', ' ').title() for v in violations]
            rationale.append(f"Detected issues: {', '.join(violation_names)}")

        # Add policy violations
        if policy_violations:
            for pv in policy_violations:
                if 'auto_block' in pv:
                    _, violation = pv.split(':')
                    rationale.append(f"Auto-blocked: {violation.replace('_', ' ').title()}")
                elif 'threshold' in pv:
                    rationale.append(f"Exceeded safety threshold: {pv}")

        # Add component insights
        high_scores = [(k, v) for k, v in component_scores.items() if v > 0.5]
        if high_scores:
            for component, score in high_scores:
                rationale.append(f"High {component} signal: {score:.2f}")

        # Language note
        if detected_language != 'en':
            rationale.append(f"Content language: {detected_language}")

        # Build summary
        if not rationale:
            if decision == ModerationDecision.APPROVE:
                details = "No policy violations detected."
            else:
                details = "Further review required."
        else:
            details = " | ".join(rationale[:3])

        explanation = self.templates[decision].format(details=details)

        return explanation, rationale


class KeywordMatcher:
    """
    Lightweight keyword-based detection (SUPPLEMENTARY ONLY).

    This is NOT the primary detection mechanism. The main detection is done by:
    1. Intent Classification (BART-MNLI)
    2. Toxicity Detection (Detoxify)
    3. Semantic Similarity (FAISS)

    Keywords are used only to catch obvious edge cases that ML might miss.
    """

    def __init__(self):
        self._load_keywords()

    def _load_keywords(self):
        """Load minimal critical keyword lists - only for edge cases"""
        # MINIMAL keywords - let ML models do the heavy lifting
        self.critical_keywords = {
            # Only the most obvious, unambiguous violations
            'weapons': ['ar-15', 'ak-47', 'assault rifle', 'ammunition for sale'],
            'drugs': ['cocaine for sale', 'heroin available', 'meth delivery'],
            'illegal': ['stolen goods', 'fake passport', 'counterfeit money'],
            'adult': ['escort services', 'sexual services', 'happy ending massage'],
        }

    def match(self, text: str) -> Tuple[List[str], List[ViolationType]]:
        """
        Match critical keywords in text.
        Returns only keywords found - violation detection is done by ML models.
        """
        if not text:
            return [], []

        text_lower = text.lower()
        matched_keywords = []
        matched_types = []

        for category, keywords in self.critical_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    matched_keywords.append(keyword)

        # Don't return violation types - let the ML models decide
        return matched_keywords, matched_types

