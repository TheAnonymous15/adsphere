#!/usr/bin/env python3
"""
Advanced Text Moderation Pipeline
==================================

A comprehensive 10-step text moderation system for ad content.

Pipeline Steps:
1. Receive text input
2. Normalize + tokenize text
3. Detect language
4. Encode semantic embedding
5. Retrieve nearest neighbors (vector similarity)
6. Intent classification
7. Context classification
8. Feature + signal aggregation
9. Policy scoring + violation decision
10. Output decision + rationale

Models Used:
- fastText LID (language detection)
- Sentence Transformers (embeddings)
- DeBERTa-v3 / XLM-RoBERTa (classification)
- Detoxify (toxicity)
- FAISS (vector search)
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import re
import unicodedata

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent))
from model_registry import ensure_models, get_model_path


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

    # Policy evaluation
    policy_violations: List[str] = field(default_factory=list)
    policy_score: float = 1.0

    # Explanation
    explanation: str = ""
    detailed_rationale: List[str] = field(default_factory=list)

    # Processing info
    processing_time_ms: float = 0.0
    models_used: List[str] = field(default_factory=list)

    # Raw scores for debugging
    raw_scores: Dict[str, Any] = field(default_factory=dict)


class TextNormalizer:
    """Step 2: Text normalization and tokenization"""

    def __init__(self):
        self.spacy_nlp = None
        self._load_spacy()

    def _load_spacy(self):
        """Load spaCy for tokenization"""
        try:
            import spacy
            try:
                self.spacy_nlp = spacy.load("en_core_web_sm")
            except OSError:
                # Download if not available
                import subprocess
                subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
                             capture_output=True)
                self.spacy_nlp = spacy.load("en_core_web_sm")
            print("✓ spaCy loaded for tokenization")
        except Exception as e:
            print(f"⚠ spaCy not available: {e}")

    def normalize(self, text: str) -> str:
        """Normalize text for processing"""
        if not text:
            return ""

        # Unicode normalization
        text = unicodedata.normalize("NFKC", text)

        # Lowercase
        text = text.lower()

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.,!?\'-]', '', text)

        return text

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text using spaCy"""
        if self.spacy_nlp:
            doc = self.spacy_nlp(text)
            return [token.text for token in doc]
        else:
            # Fallback to simple tokenization
            return text.split()

    def extract_entities(self, text: str) -> List[Dict]:
        """Extract named entities"""
        entities = []
        if self.spacy_nlp:
            doc = self.spacy_nlp(text)
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
        return entities


class LanguageDetector:
    """Step 3: Language detection using XLM-RoBERTa (papluca/xlm-roberta-base-language-detection)"""

    # Language code mapping from model labels to ISO codes
    LANG_MAP = {
        'arabic': 'ar',
        'bulgarian': 'bg',
        'german': 'de',
        'modern greek': 'el',
        'english': 'en',
        'spanish': 'es',
        'french': 'fr',
        'hindi': 'hi',
        'italian': 'it',
        'japanese': 'ja',
        'dutch': 'nl',
        'polish': 'pl',
        'portuguese': 'pt',
        'russian': 'ru',
        'swahili': 'sw',
        'thai': 'th',
        'turkish': 'tr',
        'urdu': 'ur',
        'vietnamese': 'vi',
        'chinese': 'zh',
    }

    def __init__(self):
        self.classifier = None
        self._load_model()

    def _load_model(self):
        """Load XLM-RoBERTa language detection model from HuggingFace"""
        try:
            from transformers import pipeline

            self.classifier = pipeline(
                "text-classification",
                model="papluca/xlm-roberta-base-language-detection",
                device=-1,  # CPU
                top_k=1
            )
            print("✓ XLM-RoBERTa Language Detector loaded (papluca/xlm-roberta-base-language-detection)")

        except Exception as e:
            print(f"⚠ XLM-RoBERTa language detector not available: {e}")
            print("  Falling back to heuristic detection")
            self.classifier = None

    def detect(self, text: str) -> Tuple[str, float]:
        """Detect language of text"""
        if not text or len(text.strip()) < 3:
            return "en", 0.5

        if self.classifier:
            try:
                # Truncate text to avoid issues with very long inputs
                text_truncated = text[:512].replace('\n', ' ')

                result = self.classifier(text_truncated)

                # Handle different output formats
                if isinstance(result, list) and len(result) > 0:
                    if isinstance(result[0], list):
                        # top_k returns list of lists
                        top_result = result[0][0]
                    else:
                        top_result = result[0]

                    label = top_result.get('label', 'english').lower()
                    confidence = float(top_result.get('score', 0.5))

                    # Map to ISO language code
                    lang_code = self.LANG_MAP.get(label, label[:2])

                    return lang_code, confidence

            except Exception as e:
                print(f"⚠ Language detection error: {e}")

        # Fallback: simple heuristic
        return self._fallback_detect(text)

    def _fallback_detect(self, text: str) -> Tuple[str, float]:
        """Simple fallback language detection"""
        # Check for common language patterns
        text_lower = text.lower()

        # Spanish indicators
        if any(w in text_lower for w in ['está', 'está', 'qué', 'cómo', 'para']):
            return "es", 0.7

        # French indicators
        if any(w in text_lower for w in ['est', 'sont', 'avec', 'pour', 'dans']):
            return "fr", 0.7

        # German indicators
        if any(w in text_lower for w in ['ist', 'sind', 'und', 'für', 'auf']):
            return "de", 0.7

        # Swahili indicators
        if any(w in text_lower for w in ['na', 'kwa', 'ya', 'ni', 'wa']):
            return "sw", 0.7

        # Default to English
        return "en", 0.6


class SemanticEncoder:
    """Step 4: Semantic embedding using Sentence Transformers"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = None
        self.model_name = model_name
        self._load_model()

    def _load_model(self):
        """Load sentence transformer model"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            print(f"✓ Sentence Transformer loaded: {self.model_name}")
        except Exception as e:
            print(f"⚠ Sentence Transformer not available: {e}")

    def encode(self, text: str) -> Optional[List[float]]:
        """Encode text to embedding vector"""
        if not self.model or not text:
            return None

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            print(f"⚠ Encoding error: {e}")
            return None

    def encode_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Encode multiple texts"""
        if not self.model or not texts:
            return None

        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            print(f"⚠ Batch encoding error: {e}")
            return None


class VectorDatabase:
    """Step 5: Vector similarity search using FAISS"""

    def __init__(self, dimension: int = 384):
        self.index = None
        self.dimension = dimension
        self.violation_texts = []
        self.violation_labels = []
        self._initialize()

    def _initialize(self):
        """Initialize FAISS index with known violation patterns"""
        try:
            import faiss
            import numpy as np

            # Create index
            self.index = faiss.IndexFlatL2(self.dimension)

            # Add known violation patterns (will be populated from database)
            self._load_violation_patterns()

            print(f"✓ FAISS index initialized (dim={self.dimension})")
        except ImportError:
            print("⚠ FAISS not available - vector search disabled")
        except Exception as e:
            print(f"⚠ FAISS error: {e}")

    def _load_violation_patterns(self):
        """Load known violation text patterns for semantic matching"""
        # Comprehensive violation patterns for FAISS similarity search
        # These will be encoded and used to find semantically similar content
        self.violation_texts = [
            # WEAPONS
            "buy guns cheap firearms for sale",
            "sell weapons illegally black market",
            "assault rifles ammunition available",
            "handguns pistols revolvers for sale",

            # DRUGS
            "drugs for sale cocaine heroin meth",
            "buy marijuana weed cannabis online",
            "prescription pills opioids available",
            "drug dealer fast delivery discrete",

            # SCAM
            "get rich quick guaranteed returns",
            "double your money investment opportunity",
            "wire transfer western union urgent",
            "lottery winner inheritance claim now",
            "miracle weight loss lose pounds fast",
            "work from home make thousands daily",

            # SEXUAL / ADULT SERVICES
            "escort services girls available call",
            "adult entertainment sexual services",
            "nude pictures videos onlyfans content",
            "massage happy ending full service",

            # VIOLENCE
            "kill someone murder for hire",
            "beat hurt attack assault revenge",
            "torture harm violence threat",
            "looking to hire hitman",

            # HATE SPEECH
            "hate foreigners racist movement",
            "kill jews muslims destroy them",
            "white power nazi supremacy",
            "racial slurs discriminate",

            # ILLEGAL / STOLEN GOODS
            "stolen items no receipts cheap",
            "fake documents passport identity",
            "counterfeit money credit cards",
            "hack accounts passwords data",
            "human trafficking exploitation",
            "pirated software movies illegal",

            # SPAM
            "click here urgent act now limited",
            "amazing deal buy now dont miss",
            "free money guaranteed winner",
        ]

        self.violation_labels = [
            # WEAPONS (4)
            ViolationType.WEAPONS,
            ViolationType.WEAPONS,
            ViolationType.WEAPONS,
            ViolationType.WEAPONS,

            # DRUGS (4)
            ViolationType.DRUGS,
            ViolationType.DRUGS,
            ViolationType.DRUGS,
            ViolationType.DRUGS,

            # SCAM (6)
            ViolationType.SCAM,
            ViolationType.SCAM,
            ViolationType.SCAM,
            ViolationType.SCAM,
            ViolationType.SCAM,
            ViolationType.SCAM,

            # SEXUAL (4)
            ViolationType.SEXUAL,
            ViolationType.SEXUAL,
            ViolationType.SEXUAL,
            ViolationType.SEXUAL,

            # VIOLENCE (4)
            ViolationType.VIOLENCE,
            ViolationType.VIOLENCE,
            ViolationType.VIOLENCE,
            ViolationType.VIOLENCE,

            # HATE SPEECH (4)
            ViolationType.HATE_SPEECH,
            ViolationType.HATE_SPEECH,
            ViolationType.HATE_SPEECH,
            ViolationType.HATE_SPEECH,

            # ILLEGAL (6)
            ViolationType.ILLEGAL,
            ViolationType.ILLEGAL,
            ViolationType.ILLEGAL,
            ViolationType.ILLEGAL,
            ViolationType.ILLEGAL,
            ViolationType.ILLEGAL,

            # SPAM (3)
            ViolationType.SPAM,
            ViolationType.SPAM,
            ViolationType.SPAM,
        ]

    def add_vectors(self, embeddings: List[List[float]], labels: List[ViolationType]):
        """Add violation embeddings to index"""
        if not self.index:
            return

        import numpy as np
        vectors = np.array(embeddings, dtype=np.float32)
        self.index.add(vectors)
        self.violation_labels.extend(labels)

    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict]:
        """Search for similar violation patterns"""
        if not self.index or not query_embedding:
            return []

        try:
            import numpy as np
            query = np.array([query_embedding], dtype=np.float32)
            distances, indices = self.index.search(query, min(k, self.index.ntotal))

            results = []
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                if idx >= 0 and idx < len(self.violation_labels):
                    results.append({
                        "rank": i + 1,
                        "distance": float(dist),
                        "similarity": 1.0 / (1.0 + float(dist)),
                        "violation_type": self.violation_labels[idx].value,
                        "text": self.violation_texts[idx] if idx < len(self.violation_texts) else ""
                    })
            return results
        except Exception as e:
            print(f"⚠ Vector search error: {e}")
            return []


class IntentClassifier:
    """Step 6: Intent classification using transformer models"""

    # Intent categories for ads - specific to distinguish actual violations from legitimate content
    INTENTS = [
        "legitimate_product_or_service",  # Normal product/service ad
        "educational_or_informational",   # News, education, discussion
        "spam_or_clickbait",              # Spam or low-quality content
        "financial_scam",                 # Money scams, get-rich-quick
        "illegal_goods_for_sale",         # Actually selling illegal items
        "sexual_services_for_sale",       # Actually selling sexual services
        "hate_or_discrimination",         # Hate or discriminatory content
        "violence_or_threat",             # Actual threats of violence
        "personal_attack",                # Targeted harassment
        "false_claims",                   # Misleading health/product claims
    ]

    def __init__(self):
        self.classifier = None
        self._load_model()

    def _load_model(self):
        """Load intent classification model"""
        try:
            from transformers import pipeline

            # Use zero-shot classification for flexibility
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1  # CPU
            )
            print("✓ Intent classifier loaded (BART-MNLI)")
        except Exception as e:
            print(f"⚠ Intent classifier not available: {e}")

    def classify(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        """Classify intent of text"""
        if not self.classifier or not text:
            return "legitimate_ad", 0.5, {}

        try:
            result = self.classifier(
                text,
                candidate_labels=self.INTENTS,
                multi_label=False
            )

            # Get top intent
            top_intent = result['labels'][0]
            top_score = result['scores'][0]

            # Create score dict
            scores = dict(zip(result['labels'], result['scores']))

            return top_intent, top_score, scores

        except Exception as e:
            print(f"⚠ Intent classification error: {e}")
            return "legitimate_ad", 0.5, {}


class ContextClassifier:
    """Step 7: Contextual toxicity classification"""

    def __init__(self):
        self.detoxify_model = None
        self.transformer_classifier = None
        self._load_models()

    def _load_models(self):
        """Load context classification models"""
        # Load Detoxify
        try:
            from detoxify import Detoxify
            self.detoxify_model = Detoxify('original')
            print("✓ Detoxify loaded for toxicity detection")
        except Exception as e:
            print(f"⚠ Detoxify not available: {e}")

        # Load transformer for additional context
        try:
            from transformers import pipeline
            self.transformer_classifier = pipeline(
                "text-classification",
                model="unitary/toxic-bert",
                device=-1
            )
            print("✓ Toxic-BERT loaded for context classification")
        except Exception as e:
            print(f"⚠ Toxic-BERT not available: {e}")

    def classify(self, text: str) -> Dict[str, float]:
        """Get toxicity scores for text"""
        scores = {
            'toxicity': 0.0,
            'severe_toxicity': 0.0,
            'obscene': 0.0,
            'threat': 0.0,
            'insult': 0.0,
            'identity_attack': 0.0
        }

        if not text:
            return scores

        # Use Detoxify
        if self.detoxify_model:
            try:
                result = self.detoxify_model.predict(text[:5000])
                scores = {k: float(v) for k, v in result.items()}
            except Exception as e:
                print(f"⚠ Detoxify error: {e}")

        return scores


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
                'toxicity': 0.70,        # Raised from 0.6
                'severe_toxicity': 0.50, # Raised from 0.4
                'threat': 0.60,          # Raised from 0.5
                'identity_attack': 0.55, # Raised from 0.5
                'obscene': 0.70,         # Raised from 0.6
                'insult': 0.75           # Raised from 0.7
            },
            # Category severity weights for final scoring
            'category_weights': {
                'weapons': 2.0,
                'drugs': 2.0,
                'violence': 1.8,
                'sexual': 1.4,           # Reduced - many legit contexts
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
        # Check both legitimate categories
        legit_product = intent_scores.get('legitimate_product_or_service', 0)
        legit_educational = intent_scores.get('educational_or_informational', 0)
        legit_score = max(legit_product, legit_educational)

        # Only apply threshold modifier for very high legitimate scores
        # This is more conservative to avoid missing actual violations
        threshold_modifier = 1.0
        if legit_score >= 0.6:  # Only for very clearly legitimate content
            threshold_modifier = 1.0 + ((legit_score - 0.6) * 0.5)  # Max 1.2x

        # =========================================================
        # STEP 1: Intent Classification (PRIMARY SIGNAL)
        # =========================================================
        intent_risk = 0.0

        # Map intents to violation types (updated labels)
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
            # Apply threshold modifier based on legitimate score
            adjusted_threshold = thresholds.get(intent, 0.4) * threshold_modifier

            # Only flag if score exceeds adjusted threshold
            if score >= adjusted_threshold:
                violations.append(violation_type)
                intent_risk = max(intent_risk, score)

        # If legitimate score is very low AND bad intent scores are present
        if legit_score < 0.3:
            # Check if any bad intent has moderate score
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

        # Apply modifier to toxicity thresholds too
        adjusted_tox_thresholds = {k: v * threshold_modifier for k, v in tox_thresholds.items()}

        component_scores['toxicity'] = max_toxicity * self.weights['toxicity']

        # Add violations based on specific toxicity scores (with adjusted thresholds)
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
        # Raise semantic threshold for legitimate content
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
        # Keywords only matter if legitimate score is low
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

        # Boost risk if multiple signals agree (cross-validation)
        signal_count = sum([
            1 if component_scores.get('intent', 0) > 0.3 else 0,
            1 if component_scores.get('toxicity', 0) > 0.3 else 0,
            1 if component_scores.get('semantic', 0) > 0.3 else 0
        ])

        if signal_count >= 2:
            # Multiple signals agree - boost confidence
            risk_score = min(1.0, risk_score * 1.2)

        # Remove duplicates from violations
        violations = list(set(violations))

        return risk_score, violations, component_scores

        return risk_score, violations, component_scores


class PolicyEvaluator:
    """Step 9: Policy scoring and violation decision"""

    def __init__(self):
        self._load_policies()

    def _load_policies(self):
        """Load moderation policies"""
        # In production, load from OPA/Rego or YAML
        self.policies = {
            'auto_block': {
                'weapons_sale': True,
                'drug_sale': True,
                'human_trafficking': True,
                'child_exploitation': True,
                'terrorism': True,
                'hate_speech': True,
                'violence_threats': True
            },
            'require_review': {
                'adult_content': True,
                'gambling': True,
                'alcohol': True,
                'tobacco': True,
                'cryptocurrency': True,
                'scam': True
            },
            'thresholds': {
                'toxicity_block': 0.85,
                'toxicity_review': 0.55,  # Raised to reduce false positives
                'risk_block': 0.70,
                'risk_review': 0.40
            },
            'category_rules': {
                'electronics': {'max_price': 100000},
                'vehicles': {'require_documentation': True},
                'real_estate': {'require_verification': True}
            }
        }

    def evaluate(
        self,
        risk_score: float,
        violations: List[ViolationType],
        toxicity_scores: Dict[str, float],
        category: Optional[str] = None,
        price: Optional[float] = None
    ) -> Tuple[ModerationDecision, float, List[str]]:
        """
        Evaluate against policies and make final decision.

        Returns:
            - decision: APPROVE, REVIEW, or BLOCK
            - confidence: confidence in decision
            - policy_violations: list of violated policies
        """
        policy_violations = []

        # Check for auto-block violations (severe categories ONLY)
        # These are unambiguously harmful content
        auto_block_violations = [
            ViolationType.WEAPONS, ViolationType.DRUGS,
            ViolationType.ILLEGAL, ViolationType.SELF_HARM,
            ViolationType.HATE_SPEECH, ViolationType.VIOLENCE,
        ]
        for violation in violations:
            if violation in auto_block_violations:
                policy_violations.append(f"auto_block:{violation.value}")

        # Check for review-required violations (moderate categories)
        # These need human review - could be legitimate in some contexts
        review_violations = [
            ViolationType.SCAM, ViolationType.SPAM,
            ViolationType.SEXUAL,  # Moved here - many legit contexts
            ViolationType.MISLEADING, ViolationType.HARASSMENT
        ]
        for violation in violations:
            if violation in review_violations:
                policy_violations.append(f"require_review:{violation.value}")

        # Check toxicity thresholds
        max_toxicity = max(toxicity_scores.values()) if toxicity_scores else 0.0
        threat_score = toxicity_scores.get('threat', 0.0)
        identity_attack = toxicity_scores.get('identity_attack', 0.0)

        # High threat or identity attack = auto block (only very high scores)
        if threat_score >= 0.8 or identity_attack >= 0.8:
            policy_violations.append(f"severe_toxicity:threat={threat_score:.2f},identity={identity_attack:.2f}")

        if max_toxicity >= self.policies['thresholds']['toxicity_block']:
            policy_violations.append(f"toxicity_threshold:{max_toxicity:.2f}")

        # Check risk threshold
        if risk_score >= self.policies['thresholds']['risk_block']:
            policy_violations.append(f"risk_threshold:{risk_score:.2f}")

        # Make decision
        # 1. Block if any auto-block violation or severe toxicity
        if any('auto_block' in p or 'severe_toxicity' in p for p in policy_violations):
            return ModerationDecision.BLOCK, 0.95, policy_violations

        if risk_score >= self.policies['thresholds']['risk_block']:
            return ModerationDecision.BLOCK, 0.9, policy_violations

        if max_toxicity >= self.policies['thresholds']['toxicity_block']:
            return ModerationDecision.BLOCK, 0.9, policy_violations

        # 2. Review if moderate violations or medium toxicity/risk
        if any('require_review' in p for p in policy_violations):
            return ModerationDecision.REVIEW, 0.75, policy_violations

        if risk_score >= self.policies['thresholds']['risk_review']:
            return ModerationDecision.REVIEW, 0.7, policy_violations

        if max_toxicity >= self.policies['thresholds']['toxicity_review']:
            return ModerationDecision.REVIEW, 0.7, policy_violations

        # 3. Review if any violations detected at all
        if violations:
            return ModerationDecision.REVIEW, 0.65, policy_violations

        # Approve if no issues
        confidence = 1.0 - risk_score
        return ModerationDecision.APPROVE, confidence, []


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
        # Keywords are just flags for the aggregator to consider
        return matched_keywords, matched_types


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
        required_models = ['detoxify', 'transformers', 'torch']
        ensure_models(required_models, verbose=False)

        # Initialize components
        self.normalizer = TextNormalizer()
        self.language_detector = LanguageDetector()
        self.semantic_encoder = SemanticEncoder()
        self.vector_db = VectorDatabase()
        self.intent_classifier = IntentClassifier()
        self.context_classifier = ContextClassifier()
        self.feature_aggregator = FeatureAggregator()
        self.policy_evaluator = PolicyEvaluator()
        self.explanation_generator = ExplanationGenerator()
        self.keyword_matcher = KeywordMatcher()

        # Index known violations
        self._index_violations()

        print("\n" + "="*60)
        print("  Text Moderation Pipeline Ready")
        print("="*60 + "\n")

    def _index_violations(self):
        """Index known violation patterns in vector DB"""
        if self.semantic_encoder.model and self.vector_db.index:
            embeddings = self.semantic_encoder.encode_batch(
                self.vector_db.violation_texts
            )
            if embeddings:
                self.vector_db.add_vectors(embeddings, self.vector_db.violation_labels)

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

        # Step 1: Already received input

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
        if self.context_classifier.detoxify_model:
            models_used.append("Detoxify")
        if self.context_classifier.transformer_classifier:
            models_used.append("Toxic-BERT")

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
            models_used=models_used,
            raw_scores={
                'risk_score': risk_score,
                'component_scores': component_scores,
                'intent_scores': intent_scores,
                'keywords_matched': matched_keywords,
                'entities': entities,
                'tokens_count': len(tokens)
            }
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


if __name__ == "__main__":
    # Test the pipeline
    print("\n" + "="*70)
    print("  TEXT MODERATION PIPELINE TEST")
    print("="*70 + "\n")

    pipeline = TextModerationPipeline()

    # Test cases
    test_cases = [
        {
            "title": "iPhone 14 Pro Max for Sale",
            "description": "Excellent condition, 256GB, comes with original box and charger."
        },
        {
            "title": "URGENT: Get Rich Quick!!!",
            "description": "Make $10,000 per day working from home! Wire transfer required. Limited time offer!"
        },
        {
            "title": "Weapons for sale",
            "description": "AR-15 rifles and ammunition. Contact for prices. Cash only."
        },
        {
            "title": "Tutoring Services",
            "description": "Math and science tutoring for high school students. $30/hour."
        },
        {
            "title": "You are stupid and I hate you",
            "description": "Die you worthless piece of garbage. I will find you."
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: {test['title'][:50]}")
        print(f"{'='*70}")

        result = pipeline.moderate_simple(test['title'], test['description'])

        print(f"\n📋 Decision: {result.decision.value.upper()}")
        print(f"🎯 Confidence: {result.confidence:.2%}")
        print(f"🌐 Language: {result.detected_language} ({result.language_confidence:.2%})")
        print(f"🎭 Intent: {result.detected_intent} ({result.intent_confidence:.2%})")

        if result.violations:
            print(f"⚠️ Violations: {', '.join(v.value for v in result.violations)}")

        if result.toxicity_scores:
            high_tox = {k: v for k, v in result.toxicity_scores.items() if v > 0.3}
            if high_tox:
                print(f"☢️ Toxicity: {high_tox}")

        print(f"\n💬 {result.explanation}")
        print(f"⏱️ Processing time: {result.processing_time_ms:.1f}ms")
        print(f"🤖 Models used: {', '.join(result.models_used)}")

