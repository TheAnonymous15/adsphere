"""
Decision Engine - Risk scoring and moderation decisions
"""
from typing import Dict, Tuple, List
from app.core.config import settings


class DecisionEngine:
    """
    Implements the risk matrix and decision logic.

    Evaluates category scores against thresholds to produce:
    - decision: "approve", "review", "block"
    - risk_level: "low", "medium", "high", "critical"
    """

    # Category thresholds
    THRESHOLDS = {
        "nudity": {
            "approve": settings.THRESHOLD_NUDITY_APPROVE,
            "review": settings.THRESHOLD_NUDITY_REVIEW,
            "reject": settings.THRESHOLD_NUDITY_REJECT
        },
        "sexual_content": {
            "approve": settings.THRESHOLD_SEXUAL_APPROVE,
            "review": settings.THRESHOLD_SEXUAL_REVIEW,
            "reject": settings.THRESHOLD_SEXUAL_REJECT
        },
        "violence": {
            "approve": settings.THRESHOLD_VIOLENCE_APPROVE,
            "review": settings.THRESHOLD_VIOLENCE_REVIEW,
            "reject": settings.THRESHOLD_VIOLENCE_REJECT
        },
        "weapons": {
            "approve": settings.THRESHOLD_WEAPONS_APPROVE,
            "review": settings.THRESHOLD_WEAPONS_REVIEW,
            "reject": settings.THRESHOLD_WEAPONS_REJECT
        },
        "blood": {
            "approve": settings.THRESHOLD_BLOOD_APPROVE,
            "review": settings.THRESHOLD_BLOOD_REVIEW,
            "reject": settings.THRESHOLD_BLOOD_REJECT
        },
        "hate": {
            "approve": settings.THRESHOLD_HATE_APPROVE,
            "review": settings.THRESHOLD_HATE_REVIEW,
            "reject": settings.THRESHOLD_HATE_REJECT
        },
        "self_harm": {
            "approve": settings.THRESHOLD_SELF_HARM_APPROVE,
            "review": settings.THRESHOLD_SELF_HARM_REVIEW,
            "reject": settings.THRESHOLD_SELF_HARM_REJECT
        },
        "spam": {
            "approve": 0.5,   # Approve if spam score < 50%
            "review": 0.6,    # Review if spam 50-98%
            "reject": 0.98    # Block only if spam > 98%
        },
        "scam_fraud": {
            "approve": 0.4,   # Approve if scam score < 40%
            "review": 0.5,    # Review if scam 40-90%
            "reject": 0.9     # Block only if scam > 90%
        },
        "drugs": {
            "approve": 0.3,  # Approve if drugs < 30%
            "review": 0.5,   # Review if drugs 30-70%
            "reject": 0.7    # Block if drugs > 70%
        },
    }

    # Critical categories (any violation = block)
    CRITICAL_CATEGORIES = ["minors", "csam", "terrorism", "self_harm"]

    @staticmethod
    def decide(category_scores: Dict[str, float]) -> Tuple[str, str, List[str], List[str]]:
        """
        Make moderation decision based on category scores.

        Args:
            category_scores: Dict of {category: score (0.0-1.0)}

        Returns:
            Tuple of (decision, risk_level, flags, reasons)
            - decision: "approve", "review", "block"
            - risk_level: "low", "medium", "high", "critical"
            - flags: List of flagged categories
            - reasons: Human-readable explanations
        """
        decision = "approve"
        risk_level = "low"
        flags = []
        reasons = []

        # Check critical categories first
        for category in DecisionEngine.CRITICAL_CATEGORIES:
            if category in category_scores and category_scores[category] > 0.05:
                decision = "block"
                risk_level = "critical"
                flags.append(category)
                reasons.append(f"Critical violation: {category} detected")
                return decision, risk_level, flags, reasons

        # Evaluate each category against thresholds
        for category, score in category_scores.items():
            if category in DecisionEngine.CRITICAL_CATEGORIES:
                continue  # Already handled

            thresholds = DecisionEngine.THRESHOLDS.get(category)
            if not thresholds:
                continue

            if score >= thresholds["reject"]:
                # Block
                decision = "block"
                risk_level = "critical"
                flags.append(category)
                reasons.append(f"{category.capitalize()}: {score:.2f} exceeds block threshold ({thresholds['reject']})")
                break  # One block is enough

            elif score >= thresholds["review"]:
                # Review
                if decision != "block":
                    decision = "review"
                    risk_level = "high"
                flags.append(category)
                reasons.append(f"{category.capitalize()}: {score:.2f} exceeds review threshold ({thresholds['review']})")

            elif score >= thresholds["approve"]:
                # Borderline - flag but don't change decision
                if risk_level == "low":
                    risk_level = "medium"
                flags.append(category)
                reasons.append(f"{category.capitalize()}: {score:.2f} is borderline")

        # If no reasons, everything is clean
        if not reasons:
            reasons.append("All categories below safety thresholds")

        return decision, risk_level, flags, reasons

    @staticmethod
    def calculate_global_score(category_scores: Dict[str, float]) -> float:
        """
        Calculate overall safety score (0.0 = unsafe, 1.0 = safe)

        Uses weighted average with emphasis on critical categories.
        """
        if not category_scores:
            return 1.0

        # Weight critical categories higher
        weights = {
            "nudity": 1.5,
            "sexual_content": 1.5,
            "minors": 3.0,
            "csam": 5.0,
            "violence": 1.2,
            "weapons": 1.3,
            "blood": 1.1,
            "hate": 1.4,
            "self_harm": 2.0,
            "terrorism": 3.0,
        }

        total_weighted_score = 0.0
        total_weight = 0.0

        for category, score in category_scores.items():
            weight = weights.get(category, 1.0)
            # Invert score: high violation score → low safety score
            safety = 1.0 - score
            total_weighted_score += safety * weight
            total_weight += weight

        if total_weight == 0:
            return 1.0

        global_score = total_weighted_score / total_weight
        return max(0.0, min(1.0, global_score))

