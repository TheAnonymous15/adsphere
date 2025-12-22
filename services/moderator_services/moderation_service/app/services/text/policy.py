"""
Policy Evaluator
================

Step 9: Policy scoring and final moderation decision.
"""

from typing import Dict, List, Optional, Tuple
from uuid import uuid4
from datetime import datetime

from .models import ModerationDecision, ViolationType


class PolicyEvaluator:
    """Step 9: Policy scoring and violation decision"""

    def __init__(self):
        self.version = "1.1.0"
        self._load_policies()

    def _load_policies(self):
        """Load moderation rules. In production, load from Rego or YAML."""
        self.policies = {
            "thresholds": {
                "toxicity_block": 0.85,
                "toxicity_review": 0.55,
                "risk_block": 0.70,
                "risk_review": 0.40,
            },

            "auto_block": {
                ViolationType.WEAPONS,
                ViolationType.DRUGS,
                ViolationType.ILLEGAL,
                ViolationType.SELF_HARM,
                ViolationType.HATE_SPEECH,
                ViolationType.VIOLENCE,
            },

            "review": {
                ViolationType.SCAM,
                ViolationType.SPAM,
                ViolationType.SEXUAL,
                ViolationType.MISLEADING,
                ViolationType.HARASSMENT,
            },

            "category_rules": {
                "electronics": {"max_price": 100000},
                "vehicles": {"require_documentation": True},
                "real_estate": {"require_verification": True},
            }
        }

    def _record(self, rule_id: str, severity: str, message: str) -> Dict:
        """Return structured violation dict"""
        return {
            "id": rule_id,
            "severity": severity,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "event_id": str(uuid4())
        }

    def evaluate(
        self,
        risk_score: float,
        violations: List[ViolationType],
        toxicity_scores: Dict[str, float],
        category: Optional[str] = None,
        price: Optional[float] = None
    ) -> Tuple[ModerationDecision, float, List[Dict]]:
        """
        Evaluate against policies and generate moderation decision.

        Returns:
            - ModerationDecision enum
            - confidence score
            - list of structured policy violations
        """

        policy_violations: List[Dict] = []

        # --- rule 1: direct auto-block categories ----
        for v in violations:
            if v in self.policies["auto_block"]:
                policy_violations.append(
                    self._record(
                        rule_id=f"auto_block.{v.value}",
                        severity="high",
                        message=f"Detected prohibited category: {v.value}"
                    )
                )

        # --- rule 2: moderate review-required categories ----
        for v in violations:
            if v in self.policies["review"]:
                policy_violations.append(
                    self._record(
                        rule_id=f"review.{v.value}",
                        severity="medium",
                        message=f"Content flagged for potential concern: {v.value}"
                    )
                )

        # --- rule 3: evaluate toxicity ----
        max_tox = max(toxicity_scores.values()) if toxicity_scores else 0.0
        threat = toxicity_scores.get("threat", 0.0)
        identity_attack = toxicity_scores.get("identity_attack", 0.0)

        if threat >= 0.8 or identity_attack >= 0.8:
            policy_violations.append(
                self._record(
                    rule_id="toxicity.severe",
                    severity="high",
                    message=f"Severe toxicity threat={threat:.2f} identity_attack={identity_attack:.2f}"
                )
            )

        if max_tox >= self.policies["thresholds"]["toxicity_block"]:
            policy_violations.append(
                self._record(
                    rule_id="toxicity.max_threshold",
                    severity="high",
                    message=f"Toxicity score {max_tox:.2f} exceeds block threshold"
                )
            )

        # ---- rule 4: risk scoring thresholds ----
        if risk_score >= self.policies["thresholds"]["risk_block"]:
            policy_violations.append(
                self._record(
                    rule_id="risk.block",
                    severity="high",
                    message=f"Risk score {risk_score:.2f} exceeds block threshold"
                )
            )

        # ---- rule 5: category rules ----
        if category and price:
            rules = self.policies["category_rules"].get(category)
            if rules and "max_price" in rules and price > rules["max_price"]:
                policy_violations.append(
                    self._record(
                        rule_id=f"category.{category}.max_price",
                        severity="medium",
                        message=f"Price {price} exceeds category limit {rules['max_price']}"
                    )
                )

        # -----------------------------
        ### FINAL DECISION LOGIC
        # -----------------------------

        # Any HIGH severity rule → block
        if any(v["severity"] == "high" for v in policy_violations):
            return ModerationDecision.BLOCK, 0.95, policy_violations

        # Rule-based review triggers
        if any(v["severity"] == "medium" for v in policy_violations):
            return ModerationDecision.REVIEW, 0.75, policy_violations

        # Risk-only thresholds
        if risk_score >= self.policies["thresholds"]["risk_review"]:
            return ModerationDecision.REVIEW, 0.70, policy_violations

        if max_tox >= self.policies["thresholds"]["toxicity_review"]:
            return ModerationDecision.REVIEW, 0.70, policy_violations

        # If any violation exists at all → review
        if violations:
            return ModerationDecision.REVIEW, 0.60, policy_violations

        # Otherwise approve
        confidence = 1.0 - risk_score
        return ModerationDecision.APPROVE, confidence, policy_violations
