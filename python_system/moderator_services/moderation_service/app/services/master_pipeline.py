"""
Master Pipeline Orchestrator
Coordinates all moderation services and makes final decisions
"""
from typing import Dict, List, Optional
import time
import uuid
from datetime import datetime

from app.services.text_rules import TextRulesEngine
from app.services.text_detoxify import DetoxifyService
from app.services.text.text_moderation_pipeline import (
    TextModerationPipeline,
    TextModerationInput,
    ModerationDecision,
    ViolationType
)
from app.services.nsfw_detector import NSFWDetector
from app.services.yolo_violence import ViolenceDetector
from app.services.yolo_weapons import WeaponDetector
from app.services.blood_detector import BloodDetector
from app.services.ocr_paddle import OCRService
from app.services.asr_whisper import ASRService
from app.services.video_processor import VideoProcessor
from app.services.contextual_intelligence import ContextualIntelligence
from app.core.decision_engine import DecisionEngine
from app.core.hashing import ContentHasher
from app.models.schemas import CategoryScores, ModerationRequest
from app.utils.logging import audit_logger, app_logger

# AI Search Assistant
try:
    from app.services.search_assisatnt.search_service import SearchService
    SEARCH_SERVICE_AVAILABLE = True
except ImportError as e:
    app_logger.warning(f"SearchService not available: {e}")
    SEARCH_SERVICE_AVAILABLE = False


class MasterModerationPipeline:
    """
    Master orchestrator for all moderation workflows.

    Coordinates:
    - Rule-based pre-screening
    - ML model inference
    - Score aggregation
    - Decision making
    - Audit logging
    """

    def __init__(self):
        # Initialize all services
        self.text_rules = TextRulesEngine()
        self.text_detoxify = DetoxifyService()  # Keep as fallback

        # NEW: Initialize comprehensive text moderation pipeline
        try:
            self.text_pipeline = TextModerationPipeline()
            self.use_new_text_pipeline = True
            app_logger.info("New TextModerationPipeline loaded successfully")
        except Exception as e:
            app_logger.warning(f"TextModerationPipeline failed to load, using fallback: {e}")
            self.text_pipeline = None
            self.use_new_text_pipeline = False

        # Optional services - don't crash if they fail
        try:
            self.nsfw_detector = NSFWDetector()
        except Exception as e:
            app_logger.warning(f"NSFWDetector failed to load: {e}")
            self.nsfw_detector = None

        try:
            self.violence_detector = ViolenceDetector()
        except Exception as e:
            app_logger.warning(f"ViolenceDetector failed to load: {e}")
            self.violence_detector = None

        try:
            self.weapon_detector = WeaponDetector()
        except Exception as e:
            app_logger.warning(f"WeaponDetector failed to load: {e}")
            self.weapon_detector = None

        try:
            self.blood_detector = BloodDetector()
        except Exception as e:
            app_logger.warning(f"BloodDetector failed to load: {e}")
            self.blood_detector = None

        try:
            self.ocr_service = OCRService()
        except Exception as e:
            app_logger.warning(f"OCRService failed to load: {e}")
            self.ocr_service = None

        try:
            self.asr_service = ASRService()
        except Exception as e:
            app_logger.warning(f"ASRService failed to load: {e}")
            self.asr_service = None

        try:
            self.video_processor = VideoProcessor()
        except Exception as e:
            app_logger.warning(f"VideoProcessor failed to load: {e}")
            self.video_processor = None

        self.content_hasher = ContentHasher()

        # Contextual intelligence for intent-aware moderation
        self.contextual_intelligence = ContextualIntelligence()

        # AI Search Assistant for category matching
        if SEARCH_SERVICE_AVAILABLE:
            try:
                self.search_service = SearchService()
                app_logger.info("SearchService loaded successfully")
            except Exception as e:
                app_logger.warning(f"SearchService failed to load: {e}")
                self.search_service = None
        else:
            self.search_service = None

        app_logger.info("Master pipeline initialized")

    def moderate_text(
        self,
        title: str,
        description: str,
        category: str = "general",
        user_context: Optional[Dict] = None
    ) -> Dict:
        """
        Moderate text-only content using the comprehensive text moderation pipeline.

        Flow:
        1. Use new TextModerationPipeline (XLM-RoBERTa, Sentence Transformers, FAISS, etc.)
        2. Fall back to rule-based + Detoxify if new pipeline unavailable
        3. Decision engine
        4. Audit logging
        """
        start_time = time.time()
        audit_id = self._generate_audit_id()

        # Use the new comprehensive text moderation pipeline if available
        if self.use_new_text_pipeline and self.text_pipeline:
            return self._moderate_text_with_new_pipeline(
                title, description, category, user_context, audit_id, start_time
            )
        else:
            # Fallback to old method
            return self._moderate_text_legacy(
                title, description, category, user_context, audit_id, start_time
            )

    def _moderate_text_with_new_pipeline(
        self,
        title: str,
        description: str,
        category: str,
        user_context: Optional[Dict],
        audit_id: str,
        start_time: float
    ) -> Dict:
        """
        Use the new comprehensive TextModerationPipeline.

        This pipeline includes:
        - XLM-RoBERTa language detection (20 languages including Swahili)
        - Sentence Transformers for semantic embeddings
        - FAISS vector similarity search
        - BART-MNLI intent classification
        - Detoxify toxicity detection
        - Toxic-BERT context classification
        - Policy evaluation with configurable thresholds
        """
        # Create input for the pipeline
        input_data = TextModerationInput(
            title=title,
            description=description,
            category=category
        )

        # Run the comprehensive moderation
        result = self.text_pipeline.moderate(input_data)

        # Map violation types to category scores
        category_scores = CategoryScores()

        # Map toxicity scores
        if result.toxicity_scores:
            category_scores.hate = result.toxicity_scores.get('toxicity', 0.0)
            category_scores.self_harm = result.toxicity_scores.get('identity_attack', 0.0) * 0.5

        # Map violations to category scores
        for violation in result.violations:
            if violation == ViolationType.WEAPONS:
                category_scores.weapons = max(category_scores.weapons, 0.9)
            elif violation == ViolationType.DRUGS:
                category_scores.drugs = max(category_scores.drugs, 0.9)
            elif violation == ViolationType.VIOLENCE:
                category_scores.violence = max(category_scores.violence, 0.9)
            elif violation == ViolationType.HATE_SPEECH:
                category_scores.hate = max(category_scores.hate, 0.9)
            elif violation == ViolationType.SEXUAL:
                category_scores.sexual_content = max(category_scores.sexual_content, 0.8)
            elif violation == ViolationType.SCAM:
                category_scores.scam_fraud = max(category_scores.scam_fraud, 0.7)
                category_scores.spam = max(category_scores.spam, 0.6)
            elif violation == ViolationType.SPAM:
                category_scores.spam = max(category_scores.spam, 0.8)
            elif violation == ViolationType.ILLEGAL:
                category_scores.scam_fraud = max(category_scores.scam_fraud, 0.9)
            elif violation == ViolationType.SELF_HARM:
                category_scores.self_harm = max(category_scores.self_harm, 0.9)

        # Build AI sources from the pipeline
        ai_sources = {
            'text_moderation_pipeline': {
                'model_name': 'TextModerationPipeline',
                'score': 1.0 - result.policy_score,  # Convert to risk score
                'details': {
                    'models_used': result.models_used,
                    'detected_language': result.detected_language,
                    'language_confidence': result.language_confidence,
                    'detected_intent': result.detected_intent,
                    'intent_confidence': result.intent_confidence,
                    'violations': [v.value for v in result.violations],
                    'semantic_flags': result.semantic_flags,
                }
            }
        }

        # Add toxicity details
        if result.toxicity_scores:
            ai_sources['detoxify'] = {
                'model_name': 'detoxify',
                'score': result.toxicity_scores.get('toxicity', 0.0),
                'details': result.toxicity_scores
            }

        # Map decision
        decision = result.decision.value  # "approve", "review", or "block"

        # Determine risk level based on decision
        if decision == "block":
            risk_level = "critical" if result.confidence > 0.9 else "high"
        elif decision == "review":
            risk_level = "medium"
        else:
            risk_level = "low"

        # Build flags from violations
        flags = [v.value for v in result.violations]
        if result.policy_violations:
            flags.extend(result.policy_violations)

        # Get processing time
        processing_time = result.processing_time_ms

        # Calculate global score
        scores_dict = category_scores.model_dump()
        global_score = DecisionEngine.calculate_global_score(scores_dict)

        # Audit logging
        self._log_moderation(
            audit_id=audit_id,
            decision=decision,
            risk_level=risk_level,
            category_scores=scores_dict,
            flags=flags,
            content_type="text",
            processing_time=processing_time,
            user_context=user_context
        )

        return self._build_result(
            audit_id=audit_id,
            decision=decision,
            risk_level=risk_level,
            global_score=global_score,
            category_scores=scores_dict,
            flags=flags,
            reasons=result.detailed_rationale,
            ai_sources=ai_sources,
            rules_matches=[],
            processing_time=processing_time,
            user_context=user_context
        )

    def _moderate_text_legacy(
        self,
        title: str,
        description: str,
        category: str,
        user_context: Optional[Dict],
        audit_id: str,
        start_time: float
    ) -> Dict:
        """
        Legacy text moderation using rule-based + Detoxify.
        Used as fallback when new pipeline is unavailable.
        """
        combined_text = f"{title}\n{description}"

        # Step 1: Rule-based pre-screening (fast)
        rules_result = self.text_rules.check(combined_text)

        if rules_result['should_block']:
            # Auto-block on critical rules
            empty_scores = CategoryScores().model_dump()

            return self._build_result(
                audit_id=audit_id,
                decision="block",
                risk_level="critical",
                global_score=0.0,
                category_scores=empty_scores,
                flags=rules_result['flags'],
                reasons=[f"Rule violation: {m.rule_name}" for m in rules_result['matches'][:3]],
                ai_sources={},
                rules_matches=rules_result['matches'],
                processing_time=(time.time() - start_time) * 1000
            )

        # Step 2: ML-based detection
        category_scores = CategoryScores()
        ai_sources = {}

        if combined_text.strip():
            # Detoxify
            text_scores = self.text_detoxify.analyze(combined_text)
            category_scores.hate = text_scores.get('toxicity', 0.0)
            category_scores.self_harm = text_scores.get('identity_attack', 0.0) * 0.5

            ai_sources['detoxify'] = {
                'model_name': 'detoxify',
                'score': text_scores.get('toxicity', 0.0),
                'details': text_scores
            }

            # Spam detection
            spam_score = self._detect_spam(combined_text)
            category_scores.spam = spam_score

        # Merge rule-based flags with contextual intelligence
        for match in rules_result['matches']:
            should_override, override_reason = self.contextual_intelligence.should_override_keyword_match(
                combined_text,
                match.keyword if hasattr(match, 'keyword') else str(match),
                match.category
            )

            if should_override:
                app_logger.info(f"Overriding rule match: {match.category} - {override_reason}")
                continue

            if match.category == 'violence':
                category_scores.violence = max(category_scores.violence, 0.7)
            elif match.category == 'weapons':
                category_scores.weapons = max(category_scores.weapons, 0.7)
            elif match.category == 'drugs_hard':
                category_scores.drugs = max(category_scores.drugs, 0.9)
            elif match.category == 'theft':
                category_scores.scam_fraud = max(category_scores.scam_fraud, 0.9)
            elif match.category == 'scam':
                category_scores.scam_fraud = max(category_scores.scam_fraud, 0.6)
                category_scores.spam = max(category_scores.spam, 0.7)
            elif match.category == 'adult':
                category_scores.sexual_content = max(category_scores.sexual_content, 0.6)

        # Step 3: Decision engine
        scores_dict = category_scores.model_dump()
        decision, risk_level, flags, reasons = DecisionEngine.decide(scores_dict)
        global_score = DecisionEngine.calculate_global_score(scores_dict)

        if rules_result['should_block']:
            decision = 'block'
            risk_level = 'critical'
            flags = list(set(flags + rules_result['flags']))
            rule_reasons = [f"Rule violation: {match.rule_name}" for match in rules_result['matches']]
            reasons = rule_reasons + reasons

        processing_time = (time.time() - start_time) * 1000

        self._log_moderation(
            audit_id=audit_id,
            decision=decision,
            risk_level=risk_level,
            category_scores=scores_dict,
            flags=flags + rules_result['flags'],
            content_type="text",
            processing_time=processing_time,
            user_context=user_context
        )

        return self._build_result(
            audit_id=audit_id,
            decision=decision,
            risk_level=risk_level,
            global_score=global_score,
            category_scores=scores_dict,
            flags=flags + rules_result['flags'],
            reasons=reasons,
            ai_sources=ai_sources,
            rules_matches=rules_result['matches'],
            processing_time=processing_time,
            user_context=user_context
        )

    def moderate_image(self, image_path: str, user_context: Optional[Dict] = None) -> Dict:
        """
        Moderate single image.

        Flow:
        1. Content fingerprinting
        2. NSFW detection
        3. Violence detection
        4. Weapon detection
        5. Blood detection
        6. OCR + text moderation
        7. Decision engine
        """
        start_time = time.time()
        audit_id = self._generate_audit_id()

        # Fingerprinting
        fingerprint = self.content_hasher.combined_image_fingerprint(image_path)

        category_scores = CategoryScores()
        ai_sources = {}

        # NSFW (optional)
        if self.nsfw_detector:
            try:
                nsfw_result = self.nsfw_detector.analyze_image(image_path)
                category_scores.nudity = nsfw_result.get('nudity', 0.0)
                category_scores.sexual_content = nsfw_result.get('sexual_content', 0.0)
                ai_sources['nsfw'] = {
                    'model_name': 'nsfw_detector',
                    'score': max(nsfw_result.get('nudity', 0.0), nsfw_result.get('sexual_content', 0.0)),
                    'details': nsfw_result
                }
            except Exception as e:
                app_logger.warning(f"NSFW detection failed: {e}")

        # Violence (optional)
        if self.violence_detector:
            try:
                violence_result = self.violence_detector.detect(image_path)
                category_scores.violence = violence_result.get('violence_score', 0.0)
                ai_sources['violence'] = {
                    'model_name': 'yolo_violence',
                    'score': violence_result.get('violence_score', 0.0),
                    'details': violence_result
                }
            except Exception as e:
                app_logger.warning(f"Violence detection failed: {e}")

        # Weapons (optional)
        if self.weapon_detector:
            try:
                weapon_result = self.weapon_detector.detect(image_path)
                category_scores.weapons = weapon_result.get('weapon_score', 0.0)
                ai_sources['weapons'] = {
                    'model_name': 'yolo_weapons',
                    'score': weapon_result.get('weapon_score', 0.0),
                    'details': weapon_result
                }
            except Exception as e:
                app_logger.warning(f"Weapon detection failed: {e}")

        # Blood (optional)
        if self.blood_detector:
            try:
                blood_result = self.blood_detector.detect(image_path)
                category_scores.blood = blood_result.get('blood_score', 0.0)
                ai_sources['blood'] = {
                    'model_name': 'blood_cnn',
                    'score': blood_result.get('blood_score', 0.0),
                    'details': blood_result
                }
            except Exception as e:
                app_logger.warning(f"Blood detection failed: {e}")

        # OCR + text moderation (optional)
        if self.ocr_service:
            try:
                ocr_result = self.ocr_service.extract_text(image_path)
                ocr_text = ocr_result.get('text', '')
                if ocr_text.strip():
                    text_mod = self.moderate_text("", ocr_text, user_context=user_context)
                    category_scores.hate = max(category_scores.hate, text_mod.get('category_scores', {}).get('hate', 0.0))
                    ai_sources['ocr'] = {
                        'model_name': 'paddleocr',
                        'score': len(ocr_text) / 100.0 if ocr_text else 0.0,  # Text length as score
                        'details': ocr_result
                    }
            except Exception as e:
                app_logger.warning(f"OCR failed: {e}")

        # Decision
        scores_dict = category_scores.model_dump()
        decision, risk_level, flags, reasons = DecisionEngine.decide(scores_dict)
        global_score = DecisionEngine.calculate_global_score(scores_dict)

        processing_time = (time.time() - start_time) * 1000

        self._log_moderation(
            audit_id=audit_id,
            decision=decision,
            risk_level=risk_level,
            category_scores=scores_dict,
            flags=flags,
            content_type="image",
            processing_time=processing_time,
            user_context=user_context
        )

        return self._build_result(
            audit_id=audit_id,
            decision=decision,
            risk_level=risk_level,
            global_score=global_score,
            category_scores=scores_dict,
            flags=flags,
            reasons=reasons,
            ai_sources=ai_sources,
            fingerprint=fingerprint,
            processing_time=processing_time,
            user_context=user_context
        )

    def moderate_realtime(self, request: ModerationRequest) -> Dict:
        """
        Main entry point for real-time moderation.

        Handles text + optional media in a single request.
        """
        start_time = time.time()

        # Text moderation (always)
        text_result = self.moderate_text(
            title=request.title,
            description=request.description,
            category=request.category,
            user_context=request.user.model_dump() if request.user else None
        )

        # If text is already blocked, return immediately
        if text_result['decision'] == 'block':
            return text_result

        # Media moderation (if provided)
        if request.media:
            # For MVP: just note that media exists
            # Full implementation would download and analyze
            text_result['has_media'] = True
            text_result['media_count'] = len(request.media)

        return text_result

    def _generate_audit_id(self) -> str:
        """Generate unique audit ID"""
        return f"mod-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:12]}"

    def _detect_spam(self, text: str) -> float:
        """Simple spam detection heuristic"""
        spam_keywords = [
            'click here', 'buy now', 'limited time', 'act now',
            'free money', 'guarantee', 'risk free', 'make money fast'
        ]

        text_lower = text.lower()
        matches = sum(1 for kw in spam_keywords if kw in text_lower)

        exclamation_ratio = text.count('!') / max(len(text), 1)
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)

        spam_score = min(1.0, (matches * 0.15) + (exclamation_ratio * 2) + (caps_ratio * 1.5))
        return spam_score

    def _log_moderation(self, audit_id: str, decision: str, risk_level: str,
                       category_scores: Dict, flags: List, content_type: str,
                       processing_time: float, user_context: Optional[Dict] = None):
        """Log moderation decision to audit log"""
        audit_logger.log_moderation(
            audit_id=audit_id,
            decision=decision,
            risk_level=risk_level,
            category_scores=category_scores,
            flags=flags,
            content_type=content_type,
            processing_time=processing_time,
            user_id=user_context.get('id') if user_context else None,
            company=user_context.get('company') if user_context else None,
            ad_id=user_context.get('ad_id') if user_context else None
        )

    def _build_result(self, **kwargs) -> Dict:
        """Build standardized result dict"""
        return {
            'success': True,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            **kwargs
        }

    # ===================================================================
    # AI SEARCH ASSISTANT METHODS
    # ===================================================================

    def search_categories(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.25,
        categories: Optional[List[Dict]] = None
    ) -> Dict:
        """
        AI-powered category search using semantic similarity.

        Args:
            query: User's search query (e.g., "hungry", "TV", "rent")
            top_k: Maximum number of results to return
            threshold: Minimum similarity score (0-1)
            categories: Optional custom categories to search against

        Returns:
            Dict with matching categories and scores
        """
        start_time = time.time()

        if not self.search_service:
            return {
                'success': False,
                'error': 'Search service not available',
                'query': query,
                'results': [],
                'count': 0
            }

        try:
            # Set custom categories if provided
            if categories:
                self.search_service.set_categories(categories)

            # Perform search
            result = self.search_service.search(query, top_k, threshold)
            result['processing_time_ms'] = round((time.time() - start_time) * 1000, 2)

            app_logger.debug(f"Search query '{query}' returned {result['count']} results")
            return result

        except Exception as e:
            app_logger.error(f"Search failed for query '{query}': {e}")
            return {
                'success': False,
                'error': str(e),
                'query': query,
                'results': [],
                'count': 0
            }

    def quick_search(self, query: str, top_k: int = 3) -> List[str]:
        """
        Quick search returning just category slugs.

        Args:
            query: Search term
            top_k: Max results

        Returns:
            List of matching category slugs
        """
        result = self.search_categories(query, top_k)
        if result.get('success'):
            return [r['slug'] for r in result.get('results', [])]
        return []


# Singleton instance
_pipeline_instance: Optional[MasterModerationPipeline] = None

def get_pipeline() -> MasterModerationPipeline:
    """Get or create the singleton MasterModerationPipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = MasterModerationPipeline()
    return _pipeline_instance

