"""
Audio Chunk Processor - Splits audio into chunks for parallel processing
For a 60s audio, we split into 10 chunks of 6s each and process in parallel

Each chunk is processed by a worker for:
1. Speech-to-text (Whisper ASR)
2. Toxicity analysis (Detoxify)
3. Keyword detection (banned words)
"""
import os
import sys
import asyncio
import subprocess
import tempfile
import secrets
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

# Set up paths for model_registry import
# Path: audio/audio_chunk_processor.py -> audio -> services -> app -> moderation_service -> moderator_services
CURRENT_DIR = Path(__file__).parent.resolve()
SERVICES_DIR = CURRENT_DIR.parent.resolve()
APP_DIR = SERVICES_DIR.parent.resolve()
MODERATION_SERVICE_DIR = APP_DIR.parent.resolve()
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent.resolve()

for _path in [str(MODERATOR_SERVICES_DIR), str(MODERATION_SERVICE_DIR), str(APP_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from model_registry import ensure_models

# Ensure required models are available
REQUIRED_MODELS = ['whisper', 'detoxify', 'torch']
if not ensure_models(REQUIRED_MODELS, verbose=False):
    print("⚠ AudioChunkProcessor: Some models not available")


@dataclass
class AudioChunk:
    """Represents a single audio chunk"""
    chunk_id: int
    chunk_path: str
    start_time: float  # seconds
    end_time: float    # seconds
    duration: float    # seconds


@dataclass
class ChunkAnalysisResult:
    """Analysis result for a single audio chunk"""
    chunk_id: int
    start_time: float
    end_time: float

    # Transcription
    transcription: str = ""
    language: str = "unknown"
    confidence: float = 0.0

    # Word-level timestamps
    words: List[Dict] = field(default_factory=list)

    # Toxicity scores
    toxicity_scores: Dict[str, float] = field(default_factory=dict)

    # Flags
    flags: List[str] = field(default_factory=list)
    risk_level: str = "low"

    # Processing info
    processing_time_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class AudioAnalysisResult:
    """Aggregated result from all audio chunks"""
    success: bool
    total_duration: float
    chunks_processed: int

    # Full transcription (combined from all chunks)
    full_transcription: str = ""
    detected_language: str = "unknown"

    # Aggregated toxicity (max across chunks)
    max_toxicity_scores: Dict[str, float] = field(default_factory=dict)

    # All flags from all chunks
    all_flags: List[str] = field(default_factory=list)

    # Overall risk
    risk_level: str = "low"

    # Per-chunk results
    chunk_results: List[ChunkAnalysisResult] = field(default_factory=list)

    # Timestamps of flagged content
    flagged_segments: List[Dict] = field(default_factory=list)

    # Processing stats
    total_processing_time_ms: float = 0.0
    avg_chunk_time_ms: float = 0.0
    parallel_workers: int = 0

    error: Optional[str] = None


class AudioChunker:
    """
    Splits audio into equal chunks for parallel processing.

    For a 60s audio file:
    - Split into 10 chunks of 6s each
    - Each chunk processed by a separate worker
    - Results aggregated for final analysis
    """

    def __init__(self, chunk_duration: float = 6.0, overlap: float = 0.5):
        """
        Initialize audio chunker.

        Args:
            chunk_duration: Duration of each chunk in seconds (default: 6s)
            overlap: Overlap between chunks in seconds (helps with word boundaries)
        """
        self.chunk_duration = chunk_duration
        self.overlap = overlap

    def get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration using ffprobe."""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return float(result.stdout.strip())
        except:
            return 0.0

    def split_audio(self, audio_path: str, output_dir: str, num_chunks: int = 10) -> List[AudioChunk]:
        """
        Split audio into equal chunks.

        Args:
            audio_path: Path to source audio file
            output_dir: Directory to save chunks
            num_chunks: Number of chunks to create (default: 10)

        Returns:
            List of AudioChunk objects
        """
        # Get total duration
        total_duration = self.get_audio_duration(audio_path)

        if total_duration == 0:
            return []

        # Calculate chunk duration
        chunk_duration = total_duration / num_chunks

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        chunks = []
        secure_prefix = secrets.token_hex(8)

        for i in range(num_chunks):
            start_time = i * chunk_duration
            end_time = min((i + 1) * chunk_duration + self.overlap, total_duration)
            duration = end_time - start_time

            # Generate chunk filename
            chunk_filename = f"chunk_{secure_prefix}_{i:03d}.wav"
            chunk_path = os.path.join(output_dir, chunk_filename)

            # Extract chunk using ffmpeg
            cmd = [
                "ffmpeg",
                "-i", audio_path,
                "-ss", str(start_time),
                "-t", str(duration),
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                "-y",
                chunk_path,
                "-loglevel", "error"
            ]

            try:
                subprocess.run(cmd, capture_output=True, timeout=60)

                if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 0:
                    chunks.append(AudioChunk(
                        chunk_id=i,
                        chunk_path=chunk_path,
                        start_time=start_time,
                        end_time=end_time,
                        duration=duration
                    ))
            except Exception as e:
                print(f"⚠ Failed to extract chunk {i}: {e}")

        return chunks

    def cleanup_chunks(self, chunks: List[AudioChunk]):
        """Remove temporary chunk files."""
        for chunk in chunks:
            try:
                if os.path.exists(chunk.chunk_path):
                    os.unlink(chunk.chunk_path)
            except:
                pass


# Global models for audio processing
_audio_models = {}
_audio_models_loaded = False


def _load_audio_models():
    """Load audio processing models once."""
    global _audio_models, _audio_models_loaded

    if _audio_models_loaded:
        return _audio_models

    # Whisper ASR
    try:
        import whisper
        _audio_models['whisper'] = whisper.load_model("small")
        print("✓ Whisper ASR loaded")
    except Exception as e:
        print(f"⚠ Whisper not available: {e}")
        _audio_models['whisper'] = None

    # Detoxify
    try:
        from detoxify import Detoxify
        _audio_models['detoxify'] = Detoxify('original')
        print("✓ Detoxify loaded for audio")
    except Exception as e:
        print(f"⚠ Detoxify not available: {e}")
        _audio_models['detoxify'] = None

    _audio_models_loaded = True
    return _audio_models


# =============================================================================
# MULTILINGUAL BANNED WORDS DICTIONARY
# =============================================================================
# Format: (word, category)
# Categories: violence, drugs, hate, weapons, terrorism, self_harm

BANNED_WORDS_BY_LANGUAGE = {
    # English
    'en': [
        # Violence
        ('kill', 'violence'), ('murder', 'violence'), ('attack', 'violence'),
        ('assault', 'violence'), ('stab', 'violence'), ('shoot', 'violence'),
        ('beat', 'violence'), ('strangle', 'violence'),
        # Weapons
        ('gun', 'weapons'), ('rifle', 'weapons'), ('pistol', 'weapons'),
        ('bomb', 'weapons'), ('explosive', 'weapons'), ('grenade', 'weapons'),
        # Drugs
        ('cocaine', 'drugs'), ('heroin', 'drugs'), ('meth', 'drugs'),
        ('drug deal', 'drugs'), ('marijuana', 'drugs'), ('weed', 'drugs'),
        # Terrorism
        ('terrorist', 'terrorism'), ('jihad', 'terrorism'), ('isis', 'terrorism'),
        ('al qaeda', 'terrorism'), ('extremist', 'terrorism'),
        # Self-harm
        ('suicide', 'self_harm'), ('kill myself', 'self_harm'), ('end my life', 'self_harm'),
        # Hate
        ('hate', 'hate'), ('racist', 'hate'), ('bigot', 'hate'),
    ],

    # Swahili (Kiswahili)
    'sw': [
        # Violence - Vurugu
        ('ua', 'violence'),           # kill
        ('kuua', 'violence'),         # to kill
        ('mauaji', 'violence'),       # murder/killing
        ('shambulia', 'violence'),    # attack
        ('piga', 'violence'),         # hit/beat
        ('choma', 'violence'),        # stab/burn
        ('pigana', 'violence'),       # fight
        ('vuruga', 'violence'),       # disturb violently
        ('nyonga', 'violence'),       # strangle
        ('kata', 'violence'),         # cut
        # Weapons - Silaha
        ('bunduki', 'weapons'),       # gun
        ('risasi', 'weapons'),        # bullet
        ('kisu', 'weapons'),          # knife
        ('panga', 'weapons'),         # machete
        ('bomu', 'weapons'),          # bomb
        ('silaha', 'weapons'),        # weapon
        ('rungu', 'weapons'),         # club/bludgeon
        # Drugs - Dawa za kulevya
        ('bangi', 'drugs'),           # marijuana/cannabis
        ('dawa za kulevya', 'drugs'), # drugs
        ('mihadarati', 'drugs'),      # narcotics
        ('unga', 'drugs'),            # powder (slang for drugs)
        ('heroini', 'drugs'),         # heroin
        ('kokeini', 'drugs'),         # cocaine
        # Terrorism - Ugaidi
        ('ugaidi', 'terrorism'),      # terrorism
        ('mgaidi', 'terrorism'),      # terrorist
        ('jihadi', 'terrorism'),      # jihadist
        ('mshambuliaji', 'terrorism'), # attacker
        # Self-harm - Kujidhuru
        ('kujiua', 'self_harm'),      # suicide
        ('jiue', 'self_harm'),        # kill yourself
        ('kifo', 'self_harm'),        # death (in harmful context)
        # Hate - Chuki
        ('chuki', 'hate'),            # hate
        ('ubaguzi', 'hate'),          # discrimination
        ('dharau', 'hate'),           # despise/insult
        ('tusi', 'hate'),             # insult
        ('laana', 'hate'),            # curse
        # Offensive - Matusi
        ('malaya', 'offensive'),      # prostitute (insult)
        ('mavi', 'offensive'),        # excrement
        ('mjinga', 'offensive'),      # fool/idiot
        ('pumbavu', 'offensive'),     # stupid
    ],

    # Arabic
    'ar': [
        ('قتل', 'violence'),          # kill
        ('اغتيال', 'violence'),       # assassination
        ('هجوم', 'violence'),         # attack
        ('سلاح', 'weapons'),          # weapon
        ('بندقية', 'weapons'),        # gun
        ('قنبلة', 'weapons'),         # bomb
        ('مخدرات', 'drugs'),          # drugs
        ('إرهاب', 'terrorism'),       # terrorism
        ('إرهابي', 'terrorism'),      # terrorist
        ('انتحار', 'self_harm'),      # suicide
        ('كراهية', 'hate'),           # hate
    ],

    # French
    'fr': [
        ('tuer', 'violence'),         # kill
        ('meurtre', 'violence'),      # murder
        ('attaque', 'violence'),      # attack
        ('arme', 'weapons'),          # weapon
        ('fusil', 'weapons'),         # rifle
        ('bombe', 'weapons'),         # bomb
        ('drogue', 'drugs'),          # drugs
        ('cocaïne', 'drugs'),         # cocaine
        ('terroriste', 'terrorism'), # terrorist
        ('suicide', 'self_harm'),     # suicide
        ('haine', 'hate'),            # hate
    ],

    # Spanish
    'es': [
        ('matar', 'violence'),        # kill
        ('asesinato', 'violence'),    # murder
        ('atacar', 'violence'),       # attack
        ('arma', 'weapons'),          # weapon
        ('pistola', 'weapons'),       # pistol
        ('bomba', 'weapons'),         # bomb
        ('droga', 'drugs'),           # drugs
        ('cocaína', 'drugs'),         # cocaine
        ('terrorista', 'terrorism'), # terrorist
        ('suicidio', 'self_harm'),    # suicide
        ('odio', 'hate'),             # hate
    ],

    # Portuguese
    'pt': [
        ('matar', 'violence'),        # kill
        ('assassinato', 'violence'),  # murder
        ('ataque', 'violence'),       # attack
        ('arma', 'weapons'),          # weapon
        ('bomba', 'weapons'),         # bomb
        ('droga', 'drugs'),           # drugs
        ('terrorista', 'terrorism'), # terrorist
        ('suicídio', 'self_harm'),    # suicide
        ('ódio', 'hate'),             # hate
    ],

    # Hindi
    'hi': [
        ('मारना', 'violence'),        # kill
        ('हत्या', 'violence'),        # murder
        ('हमला', 'violence'),         # attack
        ('बंदूक', 'weapons'),         # gun
        ('बम', 'weapons'),            # bomb
        ('ड्रग्स', 'drugs'),          # drugs
        ('आतंकवादी', 'terrorism'),   # terrorist
        ('आत्महत्या', 'self_harm'),   # suicide
        ('नफरत', 'hate'),             # hate
    ],

    # Chinese (Mandarin - Simplified)
    'zh': [
        ('杀', 'violence'),           # kill
        ('谋杀', 'violence'),         # murder
        ('攻击', 'violence'),         # attack
        ('枪', 'weapons'),            # gun
        ('炸弹', 'weapons'),          # bomb
        ('毒品', 'drugs'),            # drugs
        ('恐怖分子', 'terrorism'),    # terrorist
        ('自杀', 'self_harm'),        # suicide
        ('仇恨', 'hate'),             # hate
    ],
}


def _get_banned_words_for_language(language_code: str) -> List[Tuple[str, str]]:
    """
    Get banned words for a specific language.
    Falls back to English if language not supported.
    Also includes universal patterns.

    Args:
        language_code: ISO 639-1 language code (e.g., 'sw', 'en', 'ar')

    Returns:
        List of (word, category) tuples
    """
    # Get language-specific words
    lang_words = BANNED_WORDS_BY_LANGUAGE.get(language_code, [])

    # Always include English as fallback (many use English words even in local languages)
    english_words = BANNED_WORDS_BY_LANGUAGE.get('en', [])

    # Combine and deduplicate
    all_words = list(set(lang_words + english_words))

    return all_words


def _analyze_chunk_sync(chunk: AudioChunk) -> ChunkAnalysisResult:
    """
    Synchronous function to analyze a single audio chunk.
    Called by worker threads.

    Supports 99+ languages including:
    - English, Swahili, French, Spanish, Arabic, Chinese, Hindi, etc.
    - Auto-detects language per chunk
    - Language-specific banned word detection
    """
    import time
    start_time = time.time()

    result = ChunkAnalysisResult(
        chunk_id=chunk.chunk_id,
        start_time=chunk.start_time,
        end_time=chunk.end_time
    )

    if not os.path.exists(chunk.chunk_path):
        result.error = f"Chunk file not found: {chunk.chunk_path}"
        return result

    models = _load_audio_models()
    whisper_model = models.get('whisper')
    detoxify_model = models.get('detoxify')

    flags = []

    # 1. Transcribe with Whisper (auto-detects language)
    if whisper_model:
        try:
            transcription = whisper_model.transcribe(
                chunk.chunk_path,
                task="transcribe",
                verbose=False
                # language=None means auto-detect
            )

            result.transcription = transcription.get('text', '').strip()
            result.language = transcription.get('language', 'unknown')

            # Extract word-level timestamps if available
            segments = transcription.get('segments', [])
            for seg in segments:
                result.words.append({
                    'start': chunk.start_time + seg.get('start', 0),
                    'end': chunk.start_time + seg.get('end', 0),
                    'text': seg.get('text', '').strip()
                })

        except Exception as e:
            result.error = f"Transcription failed: {e}"

    # 2. Analyze toxicity (Detoxify works best with English, but provides scores for any text)
    if detoxify_model and result.transcription:
        try:
            scores = detoxify_model.predict(result.transcription)
            result.toxicity_scores = {k: float(v) for k, v in scores.items()}

            # Check thresholds
            if result.toxicity_scores.get('toxicity', 0) > 0.5:
                flags.append('toxic_speech')
            if result.toxicity_scores.get('severe_toxicity', 0) > 0.3:
                flags.append('severe_toxicity')
            if result.toxicity_scores.get('threat', 0) > 0.3:
                flags.append('threat')
            if result.toxicity_scores.get('identity_attack', 0) > 0.3:
                flags.append('hate_speech')
            if result.toxicity_scores.get('obscene', 0) > 0.5:
                flags.append('obscene')

        except Exception as e:
            pass

    # 3. Multilingual keyword detection
    if result.transcription:
        detected_lang = result.language
        text_lower = result.transcription.lower()

        # Get language-specific banned words
        banned_words = _get_banned_words_for_language(detected_lang)

        for word, category in banned_words:
            if word in text_lower:
                flags.append(f'banned_word:{category}:{word}')

    result.flags = list(set(flags))

    # Determine risk level
    max_score = max(result.toxicity_scores.values()) if result.toxicity_scores else 0.0
    if max_score >= 0.8 or 'severe_toxicity' in flags or 'hate_speech' in flags:
        result.risk_level = 'critical'
    elif max_score >= 0.5 or len(flags) >= 2:
        result.risk_level = 'high'
    elif max_score >= 0.3 or len(flags) >= 1:
        result.risk_level = 'medium'
    else:
        result.risk_level = 'low'

    result.processing_time_ms = (time.time() - start_time) * 1000

    return result


class AsyncAudioChunkProcessor:
    """
    Processes audio chunks in parallel using async workers.

    For 60s audio split into 10 chunks:
    - 10 workers process chunks simultaneously
    - Each worker: Transcribe → Toxicity → Keywords
    - Results aggregated for final decision

    Usage:
        processor = AsyncAudioChunkProcessor(num_workers=10)
        result = await processor.process_audio_async(audio_path)
    """

    def __init__(
        self,
        num_chunks: int = 10,
        chunk_duration: float = 6.0,
        max_workers: int = 10
    ):
        """
        Initialize async audio processor.

        Args:
            num_chunks: Number of chunks to split audio into
            chunk_duration: Target duration per chunk (auto-calculated if None)
            max_workers: Max parallel workers
        """
        self.num_chunks = num_chunks
        self.chunk_duration = chunk_duration
        self.max_workers = max_workers
        self.chunker = AudioChunker(chunk_duration=chunk_duration)
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    async def process_audio_async(
        self,
        audio_path: str,
        temp_dir: str = None
    ) -> AudioAnalysisResult:
        """
        Process audio file by splitting into chunks and analyzing in parallel.

        Args:
            audio_path: Path to audio file
            temp_dir: Directory for temporary chunks (auto-created if None)

        Returns:
            AudioAnalysisResult with aggregated analysis
        """
        import time
        start_time = time.time()

        # Validate audio exists
        if not os.path.exists(audio_path):
            return AudioAnalysisResult(
                success=False,
                total_duration=0,
                chunks_processed=0,
                error=f"Audio file not found: {audio_path}"
            )

        # Create temp directory for chunks
        if temp_dir is None:
            temp_dir = tempfile.mkdtemp(prefix="audio_chunks_")

        chunks = []

        try:
            # Get audio duration
            total_duration = self.chunker.get_audio_duration(audio_path)

            if total_duration == 0:
                return AudioAnalysisResult(
                    success=False,
                    total_duration=0,
                    chunks_processed=0,
                    error="Could not determine audio duration"
                )

            # Split audio into chunks
            print(f"🔊 Splitting {total_duration:.1f}s audio into {self.num_chunks} chunks...")
            chunks = self.chunker.split_audio(audio_path, temp_dir, self.num_chunks)

            if not chunks:
                return AudioAnalysisResult(
                    success=False,
                    total_duration=total_duration,
                    chunks_processed=0,
                    error="Failed to split audio into chunks"
                )

            print(f"   Created {len(chunks)} chunks, processing in parallel...")

            # Pre-load models
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self._executor, _load_audio_models)

            # Process chunks in parallel
            futures = [
                loop.run_in_executor(self._executor, _analyze_chunk_sync, chunk)
                for chunk in chunks
            ]

            chunk_results = await asyncio.gather(*futures, return_exceptions=True)

            # Filter valid results
            valid_results = []
            for i, result in enumerate(chunk_results):
                if isinstance(result, Exception):
                    print(f"   ⚠ Chunk {i} failed: {result}")
                    valid_results.append(ChunkAnalysisResult(
                        chunk_id=i,
                        start_time=chunks[i].start_time,
                        end_time=chunks[i].end_time,
                        error=str(result)
                    ))
                else:
                    valid_results.append(result)

            # Aggregate results
            aggregated = self._aggregate_results(valid_results, total_duration)

            total_time = (time.time() - start_time) * 1000
            aggregated.total_processing_time_ms = total_time
            aggregated.avg_chunk_time_ms = total_time / len(chunks) if chunks else 0
            aggregated.parallel_workers = min(self.max_workers, len(chunks))

            print(f"✅ Audio analysis complete in {total_time:.0f}ms")
            print(f"   Language: {aggregated.detected_language}, Risk: {aggregated.risk_level}")

            return aggregated

        finally:
            # Cleanup chunks
            self.chunker.cleanup_chunks(chunks)

            # Remove temp directory
            try:
                if temp_dir and os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except:
                pass

    def _aggregate_results(
        self,
        chunk_results: List[ChunkAnalysisResult],
        total_duration: float
    ) -> AudioAnalysisResult:
        """Aggregate results from all chunks."""
        if not chunk_results:
            return AudioAnalysisResult(
                success=False,
                total_duration=total_duration,
                chunks_processed=0,
                error="No chunks analyzed"
            )

        # Combine transcriptions in order
        sorted_results = sorted(chunk_results, key=lambda x: x.chunk_id)
        transcriptions = [r.transcription for r in sorted_results if r.transcription]
        full_transcription = " ".join(transcriptions)

        # Detect most common language
        languages = [r.language for r in sorted_results if r.language != "unknown"]
        detected_language = max(set(languages), key=languages.count) if languages else "unknown"

        # Aggregate toxicity (max across all chunks)
        max_toxicity = {}
        for result in chunk_results:
            for key, value in result.toxicity_scores.items():
                max_toxicity[key] = max(max_toxicity.get(key, 0.0), value)

        # Collect all flags
        all_flags = set()
        for result in chunk_results:
            all_flags.update(result.flags)

        # Collect flagged segments (with timestamps)
        flagged_segments = []
        for result in chunk_results:
            if result.flags:
                flagged_segments.append({
                    'start': result.start_time,
                    'end': result.end_time,
                    'flags': result.flags,
                    'text': result.transcription[:100] + '...' if len(result.transcription) > 100 else result.transcription,
                    'risk_level': result.risk_level
                })

        # Determine overall risk
        risk_levels = [r.risk_level for r in chunk_results]
        if 'critical' in risk_levels:
            overall_risk = 'critical'
        elif 'high' in risk_levels:
            overall_risk = 'high'
        elif 'medium' in risk_levels:
            overall_risk = 'medium'
        else:
            overall_risk = 'low'

        return AudioAnalysisResult(
            success=True,
            total_duration=total_duration,
            chunks_processed=len(chunk_results),
            full_transcription=full_transcription,
            detected_language=detected_language,
            max_toxicity_scores=max_toxicity,
            all_flags=list(all_flags),
            risk_level=overall_risk,
            chunk_results=chunk_results,
            flagged_segments=flagged_segments
        )


# Convenience function
async def analyze_audio_parallel(
    audio_path: str,
    num_chunks: int = 10
) -> AudioAnalysisResult:
    """
    Convenience function to analyze audio in parallel chunks.

    For 60s audio → 10 chunks of 6s each → 10 parallel workers

    Usage:
        result = await analyze_audio_parallel("/path/to/audio.wav", num_chunks=10)
        print(f"Transcription: {result.full_transcription}")
        print(f"Risk: {result.risk_level}")
    """
    processor = AsyncAudioChunkProcessor(num_chunks=num_chunks)
    return await processor.process_audio_async(audio_path)

