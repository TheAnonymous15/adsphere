"""
Feature Aggregator
==================

Step 8: Feature and signal aggregation with intent & context awareness.
"""

from typing import Dict, List, Tuple

from .models import ViolationType


class FeatureAggregator:
    """Step 8: Feature and signal aggregation - Intent & Context Aware"""

    def __init__(self):
        # Weights prioritize ML-based signals over keywords
        self.weights = {
            'toxicity': 1.5,      # Detoxify + Toxic-BERT
            'intent': 2.5,        # BART-MNLI zero-shot (PRIMARY)
            'semantic': 1.2,      # FAISS vector similarity
            'keyword': 0.3,       # Reduced - supplementary only
            'context': 1.0        # Additional context signals
        }
        self._load_rules()

    def _load_rules(self):
        """Load aggregation rules from config"""
        self.rules = {
            'auto_block_threshold': 0.70,
            'review_threshold': 0.35,
            'approve_threshold': 0.20,
            # Intent thresholds - tuned for balance
            'intent_thresholds': {
                'financial_scam': 0.35,
                'illegal_goods_for_sale': 0.35,
                'sexual_services_for_sale': 0.40,
                'hate_or_discrimination': 0.35,
                'violence_or_threat': 0.38,
                'spam_or_clickbait': 0.40,
                'personal_attack': 0.40,
                'false_claims': 0.42
            },
            # Toxicity thresholds - raised to reduce over-blocking
            'toxicity_thresholds': {
                'toxicity': 0.70,
                'severe_toxicity': 0.50,
                'threat': 0.60,
                'identity_attack': 0.55,
                'obscene': 0.70,
                'insult': 0.75
            },
            # Category severity weights for final scoring
            'category_weights': {
                'weapons': 2.0,
                'drugs': 2.0,
                'violence': 1.8,
                'sexual': 1.4,
                'scam': 1.5,
                'hate_speech': 1.9,
                'illegal': 2.0
            }
        }

    def aggregate(
        self,
        toxicity_scores: Dict[str, float],
        intent_scores: Dict[str, float],
        semantic_matches: List[Dict],
        keyword_flags: List[str],
        context_flags: List[str]
    ) -> Tuple[float, List[ViolationType], Dict[str, float]]:
        """
        Aggregate all signals into final risk score.

        PRIORITY ORDER:
        1. Intent classification (BART-MNLI) - PRIMARY signal
        2. Toxicity detection (Detoxify) - Confirms harmful content
        3. Semantic similarity (FAISS) - Finds similar violations
        4. Keywords - Supplementary only, used for edge cases

        Returns:
            - risk_score: 0.0 (safe) to 1.0 (dangerous)
            - violations: list of detected violation types
            - component_scores: breakdown by category
        """
        component_scores = {}
        violations = []
        thresholds = self.rules['intent_thresholds']
        tox_thresholds = self.rules['toxicity_thresholds']

        # =========================================================
        # STEP 0: Get Legitimate Intent Score (CONTEXT AWARENESS)
        # =========================================================
        legit_product = intent_scores.get('legitimate_product_or_service', 0)
        legit_educational = intent_scores.get('educational_or_informational', 0)
        legit_score = max(legit_product, legit_educational)

        # Only apply threshold modifier for very high legitimate scores
        threshold_modifier = 1.0
        if legit_score >= 0.6:
            threshold_modifier = 1.0 + ((legit_score - 0.6) * 0.5)

        # =========================================================
        # STEP 1: Intent Classification (PRIMARY SIGNAL)
        # =========================================================
        intent_risk = 0.0

        intent_to_violation = {
            'financial_scam': ViolationType.SCAM,
            'illegal_goods_for_sale': ViolationType.ILLEGAL,
            'sexual_services_for_sale': ViolationType.SEXUAL,
            'hate_or_discrimination': ViolationType.HATE_SPEECH,
            'violence_or_threat': ViolationType.VIOLENCE,
            'spam_or_clickbait': ViolationType.SPAM,
            'personal_attack': ViolationType.HARASSMENT,
            'false_claims': ViolationType.MISLEADING
        }

        for intent, violation_type in intent_to_violation.items():
            score = intent_scores.get(intent, 0)
            adjusted_threshold = thresholds.get(intent, 0.4) * threshold_modifier

            if score >= adjusted_threshold:
                violations.append(violation_type)
                intent_risk = max(intent_risk, score)

        # If legitimate score is very low AND bad intent scores are present
        if legit_score < 0.3:
            bad_intents = ['financial_scam', 'illegal_goods_for_sale', 'sexual_services_for_sale',
                          'hate_or_discrimination', 'violence_or_threat']
            for bad_intent in bad_intents:
                if intent_scores.get(bad_intent, 0) >= 0.25:
                    intent_risk = max(intent_risk, 0.5)

        component_scores['intent'] = intent_risk * self.weights['intent']

        # =========================================================
        # STEP 2: Toxicity Detection (CONFIRMATION SIGNAL)
        # =========================================================
        max_toxicity = max(toxicity_scores.values()) if toxicity_scores else 0.0
        adjusted_tox_thresholds = {k: v * threshold_modifier for k, v in tox_thresholds.items()}

        component_scores['toxicity'] = max_toxicity * self.weights['toxicity']

        if toxicity_scores.get('threat', 0) >= adjusted_tox_thresholds['threat']:
            violations.append(ViolationType.VIOLENCE)
        if toxicity_scores.get('identity_attack', 0) >= adjusted_tox_thresholds['identity_attack']:
            violations.append(ViolationType.HATE_SPEECH)
        if toxicity_scores.get('obscene', 0) >= adjusted_tox_thresholds['obscene']:
            violations.append(ViolationType.SEXUAL)
        if toxicity_scores.get('severe_toxicity', 0) >= adjusted_tox_thresholds['severe_toxicity']:
            violations.append(ViolationType.VIOLENCE)

        # =========================================================
        # STEP 3: Semantic Similarity (PATTERN MATCHING)
        # =========================================================
        semantic_risk = 0.0
        semantic_threshold = 0.5 * threshold_modifier

        if semantic_matches:
            for match in semantic_matches:
                similarity = match.get('similarity', 0)
                if similarity > semantic_threshold:
                    semantic_risk = max(semantic_risk, similarity)
                    try:
                        vtype = match.get('violation_type', 'none')
                        if vtype != 'none':
                            violations.append(ViolationType(vtype))
                    except:
                        pass

        component_scores['semantic'] = semantic_risk * self.weights['semantic']

        # =========================================================
        # STEP 4: Keyword Matching (SUPPLEMENTARY - Very Low Weight)
        # =========================================================
        if legit_score < 0.4:
            keyword_risk = min(len(keyword_flags) * 0.1, 0.3)
        else:
            keyword_risk = min(len(keyword_flags) * 0.05, 0.15)
        component_scores['keyword'] = keyword_risk * self.weights['keyword']

        # =========================================================
        # STEP 5: Calculate Final Risk Score
        # =========================================================
        total_weight = sum(self.weights.values())
        risk_score = sum(component_scores.values()) / total_weight
        risk_score = min(1.0, max(0.0, risk_score))

        # Boost risk if multiple signals agree
        signal_count = sum([
            1 if component_scores.get('intent', 0) > 0.3 else 0,
            1 if component_scores.get('toxicity', 0) > 0.3 else 0,
            1 if component_scores.get('semantic', 0) > 0.3 else 0
        ])

        if signal_count >= 2:
            risk_score = min(1.0, risk_score * 1.2)

        # Remove duplicates from violations
        violations = list(set(violations))

        return risk_score, violations, component_scores

