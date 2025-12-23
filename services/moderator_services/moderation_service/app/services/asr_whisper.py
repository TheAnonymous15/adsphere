"""
Automatic Speech Recognition using Whisper
Transcribes audio from videos to detect harmful speech
"""
import sys
from pathlib import Path
from typing import Dict, Optional
import os

# Set up paths for model_registry import
# Path: services/asr_whisper.py -> services -> app -> moderation_service -> moderator_services
CURRENT_DIR = Path(__file__).parent.resolve()
APP_DIR = CURRENT_DIR.parent.resolve()
MODERATION_SERVICE_DIR = APP_DIR.parent.resolve()
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent.resolve()

for _path in [str(MODERATOR_SERVICES_DIR), str(MODERATION_SERVICE_DIR), str(APP_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from model_registry import ensure_models

# Ensure required models are available
REQUIRED_MODELS = ['whisper', 'torch']
if not ensure_models(REQUIRED_MODELS, verbose=False):
    print("⚠ ASRService: Whisper not available")


class ASRService:
    """
    Speech-to-text using OpenAI Whisper (local).

    Transcribes video audio to detect:
    - Hate speech
    - Threats
    - Illegal offers
    - Scams
    """

    def __init__(self, model_size: str = "small"):
        """
        Initialize Whisper ASR.

        Args:
            model_size: Model size - 'tiny', 'base', 'small', 'medium', 'large'
                       (small is good balance of speed/accuracy)
        """
        self.model = None
        self.model_size = model_size
        self._load_model()

    def _load_model(self):
        """Lazy load Whisper model"""
        try:
            import whisper
            self.model = whisper.load_model(self.model_size)
            print(f"✓ Whisper ASR loaded (model={self.model_size})")
        except Exception as e:
            print(f"⚠ Whisper not available: {e}")
            print("  Install: pip install openai-whisper")

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Transcribe audio file.

        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)
            language: Language code ('en', 'es', etc.) or None for auto-detect

        Returns:
            Dict with transcription results
        """
        if self.model is None:
            return {
                "text": "",
                "language": "unknown",
                "error": "Whisper model not loaded"
            }

        if not os.path.exists(audio_path):
            return {
                "text": "",
                "language": "unknown",
                "error": "Audio file not found"
            }

        try:
            result = self.model.transcribe(
                audio_path,
                language=language,
                fp16=False  # Use FP32 for CPU compatibility
            )

            return {
                "text": result.get("text", "").strip(),
                "language": result.get("language", "unknown"),
                "segments": result.get("segments", []),
                "num_segments": len(result.get("segments", []))
            }

        except Exception as e:
            print(f"ASR error: {e}")
            return {
                "text": "",
                "language": "unknown",
                "error": str(e)
            }

    def transcribe_with_timestamps(self, audio_path: str) -> Dict[str, any]:
        """
        Transcribe with word-level timestamps.

        Args:
            audio_path: Path to audio file

        Returns:
            Dict with transcription + timestamps
        """
        result = self.transcribe(audio_path)

        if "error" in result:
            return result

        segments = result.get("segments", [])

        timestamped_text = []
        for segment in segments:
            start = segment.get("start", 0)
            end = segment.get("end", 0)
            text = segment.get("text", "").strip()

            timestamped_text.append({
                "start": start,
                "end": end,
                "text": text
            })

        return {
            "text": result.get("text", ""),
            "language": result.get("language", "unknown"),
            "timestamped_segments": timestamped_text,
            "duration": segments[-1].get("end", 0) if segments else 0
        }


class VoskASRService:
    """
    Alternative ASR using Vosk (faster, offline, good for real-time).
    """

    def __init__(self, model_path: str = None):
        """
        Initialize Vosk ASR.

        Args:
            model_path: Path to Vosk model directory
        """
        self.model = None
        self.recognizer = None
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        """Lazy load Vosk model"""
        try:
            from vosk import Model, KaldiRecognizer
            import wave

            if self.model_path and os.path.exists(self.model_path):
                self.model = Model(self.model_path)
                print(f"✓ Vosk ASR loaded: {self.model_path}")
            else:
                print("⚠ Vosk model path not provided or not found")
                print("  Download from: https://alphacephei.com/vosk/models")

        except Exception as e:
            print(f"⚠ Vosk not available: {e}")

    def transcribe(self, audio_path: str) -> Dict[str, any]:
        """
        Transcribe audio using Vosk.

        Args:
            audio_path: Path to WAV file (16kHz, mono)

        Returns:
            Dict with transcription
        """
        if self.model is None:
            return {
                "text": "",
                "error": "Vosk model not loaded"
            }

        try:
            import wave
            import json
            from vosk import KaldiRecognizer

            wf = wave.open(audio_path, "rb")

            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
                return {
                    "text": "",
                    "error": "Audio must be WAV 16kHz mono PCM"
                }

            rec = KaldiRecognizer(self.model, wf.getframerate())
            rec.SetWords(True)

            results = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    if "text" in result:
                        results.append(result["text"])

            # Final result
            final_result = json.loads(rec.FinalResult())
            if "text" in final_result:
                results.append(final_result["text"])

            full_text = " ".join(results).strip()

            return {
                "text": full_text,
                "language": "auto"  # Vosk doesn't auto-detect
            }

        except Exception as e:
            print(f"Vosk transcription error: {e}")
            return {
                "text": "",
                "error": str(e)
            }

