"""
Audio Processor - Handles audio moderation pipeline
Processes extracted audio from videos for content moderation

Input: Audio file (WAV, 16kHz mono)
Output: Transcription + toxicity analysis
"""
import os
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class AudioModerationResult:
    """Result of audio moderation"""
    success: bool
    transcription: str
    language: str
    duration_seconds: float
    toxicity_scores: Dict[str, float]
    flags: List[str]
    risk_level: str  # low, medium, high, critical
    error: Optional[str] = None
    segments: List[Dict] = None  # Timestamped segments


class AudioProcessor:
    """
    Audio moderation processor.

    Pipeline:
    1. Load audio file
    2. Transcribe using Whisper ASR
    3. Detect language
    4. Analyze transcription for toxicity
    5. Return moderation result

    Receives audio from: VideoAudioSeparator
    """

    def __init__(self, whisper_model: str = "small"):
        """Initialize audio processor."""
        self.whisper_model_name = whisper_model
        self.whisper_model = None
        self.text_moderator = None
        self._load_models()

    def _load_models(self):
        """Load ASR and text moderation models"""
        # Load Whisper for speech-to-text
        try:
            import whisper
            self.whisper_model = whisper.load_model(self.whisper_model_name)
            print(f"✓ Whisper ASR loaded (model={self.whisper_model_name})")
        except Exception as e:
            print(f"⚠ Whisper ASR not available: {e}")
            self.whisper_model = None

        # Load Detoxify for text moderation
        try:
            from detoxify import Detoxify
            self.text_moderator = Detoxify('original')
            print("✓ Detoxify loaded for audio text moderation")
        except Exception as e:
            print(f"⚠ Detoxify not available: {e}")
            self.text_moderator = None

    def process(self, audio_path: str) -> AudioModerationResult:
        """Process audio file for content moderation."""
        # Validate file
        if not os.path.exists(audio_path):
            return AudioModerationResult(
                success=False,
                transcription="",
                language="unknown",
                duration_seconds=0,
                toxicity_scores={},
                flags=[],
                risk_level="unknown",
                error=f"Audio file not found: {audio_path}"
            )

        # Step 1: Transcribe audio
        transcription_result = self._transcribe(audio_path)

        if not transcription_result['success']:
            return AudioModerationResult(
                success=False,
                transcription="",
                language="unknown",
                duration_seconds=0,
                toxicity_scores={},
                flags=[],
                risk_level="unknown",
                error=transcription_result.get('error', 'Transcription failed')
            )

        text = transcription_result['text']
        language = transcription_result['language']
        segments = transcription_result.get('segments', [])

        # Step 2: Analyze text for toxicity
        toxicity_result = self._analyze_toxicity(text)

        # Step 3: Determine risk level and flags
        flags, risk_level = self._evaluate_risk(toxicity_result)

        # Get audio duration
        duration = self._get_audio_duration(audio_path)

        return AudioModerationResult(
            success=True,
            transcription=text,
            language=language,
            duration_seconds=duration,
            toxicity_scores=toxicity_result,
            flags=flags,
            risk_level=risk_level,
            segments=segments
        )

    def _transcribe(self, audio_path: str) -> Dict:
        """Transcribe audio using Whisper."""
        if self.whisper_model is None:
            return {
                'success': False,
                'error': 'Whisper model not loaded',
                'text': '',
                'language': 'unknown'
            }

        try:
            result = self.whisper_model.transcribe(
                audio_path,
                task="transcribe",
                verbose=False
            )

            segments = []
            for seg in result.get('segments', []):
                segments.append({
                    'start': seg['start'],
                    'end': seg['end'],
                    'text': seg['text'].strip()
                })

            return {
                'success': True,
                'text': result['text'].strip(),
                'language': result.get('language', 'unknown'),
                'segments': segments
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'language': 'unknown'
            }

    def _analyze_toxicity(self, text: str) -> Dict[str, float]:
        """Analyze text for toxic content."""
        if not text or not text.strip():
            return {
                'toxicity': 0.0,
                'severe_toxicity': 0.0,
                'obscene': 0.0,
                'threat': 0.0,
                'insult': 0.0,
                'identity_attack': 0.0
            }

        if self.text_moderator is None:
            return {
                'toxicity': 0.0,
                'severe_toxicity': 0.0,
                'obscene': 0.0,
                'threat': 0.0,
                'insult': 0.0,
                'identity_attack': 0.0,
                'error': 'Detoxify not available'
            }

        try:
            scores = self.text_moderator.predict(text)
            return {k: float(v) for k, v in scores.items()}
        except Exception as e:
            print(f"Toxicity analysis error: {e}")
            return {
                'toxicity': 0.0,
                'severe_toxicity': 0.0,
                'obscene': 0.0,
                'threat': 0.0,
                'insult': 0.0,
                'identity_attack': 0.0,
                'error': str(e)
            }

    def _evaluate_risk(self, toxicity_scores: Dict[str, float]) -> tuple:
        """Evaluate risk level based on toxicity scores."""
        flags = []
        max_score = 0.0

        thresholds = {
            'toxicity': (0.5, 'toxic_speech'),
            'severe_toxicity': (0.3, 'severe_toxicity'),
            'obscene': (0.5, 'obscene_language'),
            'threat': (0.3, 'threatening'),
            'insult': (0.5, 'insulting'),
            'identity_attack': (0.3, 'hate_speech')
        }

        for category, (threshold, flag) in thresholds.items():
            score = toxicity_scores.get(category, 0.0)
            if score > threshold:
                flags.append(flag)
            max_score = max(max_score, score)

        # Determine risk level
        if max_score >= 0.8 or 'severe_toxicity' in flags or 'hate_speech' in flags:
            risk_level = 'critical'
        elif max_score >= 0.6 or len(flags) >= 2:
            risk_level = 'high'
        elif max_score >= 0.4 or len(flags) >= 1:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        return flags, risk_level

    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds"""
        try:
            import subprocess
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return float(result.stdout.strip())
        except:
            return 0.0


# Convenience function
def process_audio(audio_path: str, model_size: str = "small") -> AudioModerationResult:
    """Convenience function to process audio."""
    processor = AudioProcessor(whisper_model=model_size)
    return processor.process(audio_path)

