# Video Moderation Pipeline Architecture

## Overview

The video moderation pipeline has been restructured into modular components for better maintainability and parallel processing.

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        VIDEO MODERATION PIPELINE                            │
└─────────────────────────────────────────────────────────────────────────────┘

                              VIDEO FILE UPLOAD
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. ENTRY POINT: separate_video_audio.py                                    │
│  ═══════════════════════════════════════                                    │
│                                                                             │
│  Class: VideoAudioSeparator                                                 │
│                                                                             │
│  Responsibilities:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ✓ Validate video format (mp4, webm, mov, avi, mkv)                  │   │
│  │ ✓ Check duration limit (max 60s)                                    │   │
│  │ ✓ Check file size limit (max 100MB)                                 │   │
│  │ ✓ Create secure temp directory (256-bit hex name)                   │   │
│  │ ✓ Extract audio track to WAV (16kHz mono for Whisper)               │   │
│  │ ✓ Return SeparationResult with paths                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Output: SeparationResult {                                                 │
│    video_path: str,        // Original video for frame extraction           │
│    audio_path: str,        // Extracted audio WAV                           │
│    temp_dir: str,          // Secure temp directory                         │
│    has_audio: bool,        // Whether video has audio                       │
│    duration: float,        // Video duration                                │
│    metadata: dict          // Video metadata                                │
│  }                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                     │                                    │
                     │                                    │
         ┌───────────┘                                    └───────────┐
         │                                                            │
         ▼                                                            ▼
┌─────────────────────────────────┐              ┌─────────────────────────────────┐
│  2a. AUDIO PATH                 │              │  2b. VIDEO PATH                 │
│  ═══════════════                │              │  ═════════════                  │
│                                 │              │                                 │
│  audio_processor.py             │              │  extract_video_frames.py        │
│                                 │              │                                 │
│  Class: AudioProcessor          │              │  Class: VideoFrameExtractor     │
│                                 │              │                                 │
│  Pipeline:                      │              │  Pipeline:                      │
│  ┌─────────────────────────┐   │              │  ┌─────────────────────────┐    │
│  │ 1. Load audio file      │   │              │  │ 1. Get video metadata    │    │
│  │ 2. Whisper ASR          │   │              │  │ 2. Calculate FPS         │    │
│  │ 3. Get transcription    │   │              │  │ 3. Extract frames (2fps) │    │
│  │ 4. Detoxify analysis    │   │              │  │ 4. Save as JPG files     │    │
│  │ 5. Risk evaluation      │   │              │  │ 5. Return frame paths    │    │
│  └─────────────────────────┘   │              │  └─────────────────────────┘    │
│                                 │              │                                 │
│  Output:                        │              │  Output:                        │
│  AudioModerationResult {        │              │  FrameExtractionResult {        │
│    transcription: str,          │              │    frame_paths: List[str],      │
│    language: str,               │              │    frame_count: int,            │
│    toxicity_scores: dict,       │              │    fps_used: float,             │
│    flags: list,                 │              │    video_duration: float,       │
│    risk_level: str              │              │    resolution: tuple            │
│  }                              │              │  }                              │
└─────────────────────────────────┘              └─────────────────────────────────┘
         │                                                            │
         │                                                            │
         │                                                            ▼
         │                              ┌─────────────────────────────────────────────┐
         │                              │  3. FRAME ANALYSIS                          │
         │                              │  ═════════════════                          │
         │                              │                                             │
         │                              │  video_frame_processor.py                   │
         │                              │                                             │
         │                              │  Class: VideoFrameProcessor                 │
         │                              │                                             │
         │                              │  Analyzes each frame for:                   │
         │                              │  ┌─────────────────────────────────────┐   │
         │                              │  │ 1. NSFW Detection (nudity, sexual)  │   │
         │                              │  │ 2. Violence Detection (fights)      │   │
         │                              │  │ 3. Weapon Detection (guns, knives)  │   │
         │                              │  │ 4. Blood Detection (gore)           │   │
         │                              │  │ 5. OCR (text in frames)             │   │
         │                              │  │ 6. Object Detection (general)       │   │
         │                              │  └─────────────────────────────────────┘   │
         │                              │                                             │
         │                              │  Features:                                  │
         │                              │  • Parallel processing (ThreadPoolExecutor) │
         │                              │  • Aggregates scores across all frames      │
         │                              │  • Returns max scores per category          │
         │                              │                                             │
         │                              │  Output:                                    │
         │                              │  VideoFrameProcessorResult {                │
         │                              │    max_nsfw_score: float,                   │
         │                              │    max_violence_score: float,               │
         │                              │    max_weapon_score: float,                 │
         │                              │    max_blood_score: float,                  │
         │                              │    all_text: str (OCR),                     │
         │                              │    all_objects: list,                       │
         │                              │    all_flags: list,                         │
         │                              │    category_scores: dict                    │
         │                              │  }                                          │
         │                              └─────────────────────────────────────────────┘
         │                                                            │
         │                                                            │
         └────────────────────────────┬───────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. AGGREGATION & DECISION                                                  │
│  ═════════════════════════                                                  │
│                                                                             │
│  video_moderation_pipeline.py                                               │
│                                                                             │
│  Class: VideoModerationPipeline                                             │
│                                                                             │
│  Orchestrates all components and:                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. Merges audio toxicity with frame analysis                        │   │
│  │ 2. Combines OCR text + ASR transcription                            │   │
│  │ 3. Runs text moderation on combined text                            │   │
│  │ 4. Calculates final category_scores                                 │   │
│  │ 5. Calls DecisionEngine.decide()                                    │   │
│  │ 6. Returns final decision: approve / review / block                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Output: VideoModerationResult {                                            │
│    decision: "approve" | "review" | "block",                                │
│    risk_level: "low" | "medium" | "high" | "critical",                      │
│    global_score: float (0.0 - 1.0),                                         │
│    category_scores: dict,                                                   │
│    flags: list,                                                             │
│    reasons: list,                                                           │
│    frames_analyzed: int,                                                    │
│    audio_transcription: str,                                                │
│    processing_time_ms: float                                                │
│  }                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  5. CLEANUP                                                                 │
│  ═════════                                                                  │
│                                                                             │
│  • Delete temp directory (frames, audio)                                    │
│  • Guaranteed via finally block                                             │
│  • Secure deletion of all temporary files                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## File Structure

```
app/services/
├── video/
│   ├── __init__.py
│   ├── separate_video_audio.py   ← Entry point (first touch)
│   ├── extract_video_frames.py   ← Frame extraction (2fps)
│   └── video_frame_processor.py  ← Frame analysis (AI models)
├── audio/
│   ├── __init__.py
│   └── audio_processor.py        ← Audio transcription + toxicity
└── video_moderation_pipeline.py  ← Main orchestrator
```

## Usage Example

```python
from app.services.video_moderation_pipeline import VideoModerationPipeline

# Initialize pipeline
pipeline = VideoModerationPipeline()

# Moderate a video
result = pipeline.moderate_video("/path/to/video.mp4")

# Check result
if result.decision == 'block':
    print(f"Video blocked: {result.reasons}")
elif result.decision == 'review':
    print(f"Video needs review: {result.flags}")
else:
    print(f"Video approved with score: {result.global_score}")
```

## Configuration

Settings in `app/core/config.py`:
- `FRAME_SAMPLE_FPS = 2.0` - Frames per second to extract
- `MAX_FRAMES_PER_VIDEO = 150` - Maximum frames to analyze
- `MAX_VIDEO_DURATION_SEC = 60` - Maximum video duration
- `MAX_VIDEO_SIZE_MB = 100` - Maximum file size

## Performance

| Video Length | Frames Extracted | Processing Time |
|--------------|------------------|-----------------|
| 10 seconds   | ~20 frames       | 5-10 seconds    |
| 30 seconds   | ~60 frames       | 15-25 seconds   |
| 60 seconds   | ~120 frames      | 25-45 seconds   |

*Times depend on hardware and model availability*

