"""
Contextual Intelligence Layer for Intent-Aware Moderation

This module uses semantic understanding to determine the actual intent
of content rather than just keyword matching. It helps distinguish between:
- "Full service history" (car maintenance) vs "Full service escort" (adult)
- "Massage therapist" (professional) vs "Sensual massage" (adult)
- "Party supplies" (legitimate) vs "Party supplies" (drugs)
"""

from typing import Dict, List, Tuple
import re
from collections import defaultdict


class ContextualIntelligence:
    """
    Analyzes text context to determine true intent, reducing false positives
    from keyword-only matching.

    Uses:
    - Sentence-level context analysis
    - Word co-occurrence patterns
    - Category indicators
    - Negation handling
    """

    # Category indicators help identify true intent
    CATEGORY_INDICATORS = {
        'automotive': [
            'car', 'vehicle', 'mileage', 'engine', 'transmission', 'tires',
            'warranty', 'owner', 'miles', 'automatic', 'manual', 'sedan',
            'suv', 'truck', 'honda', 'toyota', 'ford', 'chevrolet', 'bmw',
            'fuel economy', 'clean title', 'accident', 'carfax'
        ],
        'real_estate': [
            'bedroom', 'bathroom', 'apartment', 'house', 'rent', 'lease',
            'square feet', 'sq ft', 'kitchen', 'living room', 'utilities',
            'deposit', 'landlord', 'tenant', 'downtown', 'neighborhood'
        ],
        'electronics': [
            'iphone', 'ipad', 'macbook', 'laptop', 'phone', 'tablet',
            'computer', 'gaming', 'console', 'screen', 'processor', 'ram',
            'storage', 'gb', 'sealed', 'warranty', 'charger', 'cable'
        ],
        'professional_services': [
            'licensed', 'certified', 'professional', 'experience', 'qualified',
            'degree', 'training', 'references', 'portfolio', 'consultation',
            'business', 'company', 'llc', 'inc'
        ],
        'health_wellness': [
            'therapy', 'therapist', 'wellness', 'health', 'medical',
            'licensed', 'certified', 'clinic', 'spa', 'relaxation',
            'sports massage', 'deep tissue', 'swedish', 'therapeutic'
        ]
    }

    # Suspicious patterns that indicate problematic intent
    SUSPICIOUS_PATTERNS = {
        'secrecy': [
            'no questions asked', 'discreet', 'cash only', 'untraceable',
            'off the books', 'under the table', 'no paperwork', 'anonymous',
            'secret', 'hidden', 'private', 'confidential'
        ],
        'urgency_pressure': [
            'act now', 'limited time', 'hurry', 'today only', 'expires soon',
            'dont miss', 'last chance', 'urgent', 'immediately'
        ],
        'too_good': [
            'guaranteed', 'risk free', 'no risk', '100% guaranteed',
            'miracle', 'amazing results', 'instant', 'overnight',
            'free money', 'get rich', 'easy money'
        ],
        'evasive': [
            'dm for details', 'pm for info', 'ask for price', 'contact for more',
            'inquire within', 'serious inquiries only'
        ]
    }

    def __init__(self):
        """Initialize contextual intelligence"""
        pass

    def analyze_intent(self, text: str, category: str = "") -> Dict:
        """
        Analyze the true intent of the text using contextual clues.

        Args:
            text: The full text to analyze
            category: Optional category hint

        Returns:
            Dict with:
                - primary_category: Best guess at true category
                - confidence: How confident (0-1)
                - legitimate_score: How legitimate it seems (0-1)
                - suspicious_flags: List of suspicious patterns found
                - context_keywords: Keywords with their context
        """
        text_lower = text.lower()

        # Identify category from content
        category_scores = self._score_categories(text_lower)
        primary_category = max(category_scores.items(), key=lambda x: x[1])[0] if category_scores else 'general'

        # Check for suspicious patterns
        suspicious_flags = self._detect_suspicious_patterns(text_lower)

        # Calculate legitimacy score
        legitimate_score = self._calculate_legitimacy(text_lower, category_scores, suspicious_flags)

        # Extract keywords with context
        context_keywords = self._extract_contextual_keywords(text_lower)

        return {
            'primary_category': primary_category,
            'confidence': category_scores.get(primary_category, 0.0),
            'legitimate_score': legitimate_score,
            'suspicious_flags': suspicious_flags,
            'context_keywords': context_keywords,
            'category_scores': category_scores
        }

    def should_override_keyword_match(
        self,
        text: str,
        matched_keyword: str,
        matched_category: str
    ) -> Tuple[bool, str]:
        """
        Determine if a keyword match should be overridden based on context.

        Args:
            text: Full text
            matched_keyword: The keyword that matched
            matched_category: Category it matched (e.g., 'adult')

        Returns:
            (should_override, reason)
        """
        text_lower = text.lower()

        # Get context around the keyword
        context = self._get_keyword_context(text_lower, matched_keyword)

        # Analyze the intent
        intent = self.analyze_intent(text)

        # Override rules based on context
        overrides = {
            'adult': self._check_adult_override,
            'drugs': self._check_drugs_override,
            'scam': self._check_scam_override
        }

        if matched_category in overrides:
            should_override, reason = overrides[matched_category](
                matched_keyword, context, intent
            )
            if should_override:
                return True, reason

        return False, ""

    def _score_categories(self, text: str) -> Dict[str, float]:
        """Score how well text fits each category"""
        scores = {}

        for category, indicators in self.CATEGORY_INDICATORS.items():
            matches = sum(1 for indicator in indicators if indicator in text)
            # Normalize by number of indicators
            score = matches / max(len(indicators), 1)
            if score > 0:
                scores[category] = min(score * 2, 1.0)  # Amplify but cap at 1

        return scores

    def _detect_suspicious_patterns(self, text: str) -> List[str]:
        """Detect suspicious patterns in text"""
        flags = []

        for pattern_type, patterns in self.SUSPICIOUS_PATTERNS.items():
            if any(pattern in text for pattern in patterns):
                flags.append(pattern_type)

        return flags

    def _calculate_legitimacy(
        self,
        text: str,
        category_scores: Dict[str, float],
        suspicious_flags: List[str]
    ) -> float:
        """
        Calculate how legitimate the ad appears.

        High legitimacy: Has category indicators, professional language, details
        Low legitimacy: Vague, suspicious patterns, evasive
        """
        score = 0.5  # Start neutral

        # Boost for category indicators
        if category_scores:
            score += max(category_scores.values()) * 0.3

        # Penalize for suspicious patterns
        score -= len(suspicious_flags) * 0.15

        # Boost for professional indicators
        professional_words = ['licensed', 'certified', 'professional', 'qualified', 'experienced']
        if any(word in text for word in professional_words):
            score += 0.2

        # Boost for specific details (suggests legitimate)
        if any(pattern in text for pattern in [r'\d+\s*(bedroom|bathroom)', r'\$\d+', r'\d+\s*(gb|tb)', r'\d{4}\s+\w+\s+\w+']):
            score += 0.1

        # Penalize for vagueness
        vague_words = ['various', 'many', 'stuff', 'things', 'etc', 'and more']
        vagueness = sum(1 for word in vague_words if word in text)
        score -= min(vagueness * 0.1, 0.2)

        return max(0.0, min(1.0, score))

    def _extract_contextual_keywords(self, text: str) -> Dict[str, List[str]]:
        """Extract keywords with their surrounding context"""
        # This is a simplified version - in production you'd use more sophisticated NLP
        keywords = {}

        # Split into sentences
        sentences = re.split(r'[.!?]+', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Skip very short sentences
                # Extract potential keywords (words longer than 4 chars)
                words = [w for w in sentence.split() if len(w) > 4]
                for word in words[:3]:  # Top 3 words per sentence
                    if word not in keywords:
                        keywords[word] = []
                    keywords[word].append(sentence[:100])  # Store sentence context

        return keywords

    def _get_keyword_context(self, text: str, keyword: str, window: int = 50) -> str:
        """Get text context around a keyword"""
        pos = text.find(keyword.lower())
        if pos == -1:
            return ""

        start = max(0, pos - window)
        end = min(len(text), pos + len(keyword) + window)

        return text[start:end]

    def _check_adult_override(
        self,
        keyword: str,
        context: str,
        intent: Dict
    ) -> Tuple[bool, str]:
        """Check if adult keyword should be overridden"""

        # "full service" in automotive context
        if keyword == "full service":
            if intent['primary_category'] == 'automotive':
                if any(word in context for word in ['history', 'record', 'maintenance', 'car', 'vehicle']):
                    return True, "Legitimate automotive service reference"

            if intent['primary_category'] == 'real_estate':
                if any(word in context for word in ['building', 'apartment', 'amenities']):
                    return True, "Legitimate building services reference"

        # "massage" in health/wellness context
        if keyword == "massage":
            if intent['primary_category'] == 'health_wellness':
                if intent['legitimate_score'] > 0.7:
                    if any(word in context for word in ['therapeutic', 'sports', 'deep tissue', 'licensed', 'certified']):
                        return True, "Legitimate massage therapy"

        return False, ""

    def _check_drugs_override(
        self,
        keyword: str,
        context: str,
        intent: Dict
    ) -> Tuple[bool, str]:
        """Check if drug keyword should be overridden"""

        # Medical/health context
        if intent['primary_category'] == 'health_wellness':
            medical_context = ['prescription', 'doctor', 'pharmacy', 'medical', 'treatment']
            if any(word in context for word in medical_context):
                if intent['legitimate_score'] > 0.6:
                    return True, "Medical/prescription context"

        return False, ""

    def _check_scam_override(
        self,
        keyword: str,
        context: str,
        intent: Dict
    ) -> Tuple[bool, str]:
        """Check if scam keyword should be overridden"""

        # Legitimate use of words like "guaranteed"
        if keyword in ['guarantee', 'guaranteed']:
            if intent['primary_category'] == 'automotive':
                if 'warranty' in context or 'certified' in context:
                    return True, "Legitimate warranty/guarantee reference"

        return False, ""

    def enhance_moderation_decision(
        self,
        text: str,
        initial_scores: Dict[str, float],
        matched_rules: List[Dict]
    ) -> Dict:
        """
        Enhance moderation decision with contextual intelligence.

        This adjusts scores based on intent analysis to reduce false positives
        while maintaining security.
        """
        intent = self.analyze_intent(text)

        adjustments = {
            'score_multipliers': {},
            'overridden_rules': [],
            'intent_analysis': intent
        }

        # Check each matched rule
        for rule in matched_rules:
            if 'keyword' in rule and 'category' in rule:
                should_override, reason = self.should_override_keyword_match(
                    text, rule['keyword'], rule['category']
                )

                if should_override:
                    adjustments['overridden_rules'].append({
                        'rule': rule,
                        'reason': reason
                    })

        # Adjust scores based on legitimacy
        if intent['legitimate_score'] > 0.8 and not intent['suspicious_flags']:
            # High legitimacy, low suspicion - reduce penalty scores
            adjustments['score_multipliers'] = {
                'sexual_content': 0.3,  # Reduce by 70%
                'scam_fraud': 0.5,      # Reduce by 50%
                'spam': 0.6             # Reduce by 40%
            }
        elif intent['legitimate_score'] < 0.3 or len(intent['suspicious_flags']) >= 2:
            # Low legitimacy or multiple suspicious flags - increase scrutiny
            adjustments['score_multipliers'] = {
                'scam_fraud': 1.5,  # Increase by 50%
                'spam': 1.3         # Increase by 30%
            }

        return adjustments


# Global instance
contextual_intelligence = ContextualIntelligence()

