#!/usr/bin/env python3
"""
Test Offline Video Moderation
Run moderation on local video files from sample_videos directory

Usage:
    python test_offline_video.py                    # Process all videos in sample_videos/
    python test_offline_video.py video.mp4          # Process specific video
    python test_offline_video.py /path/to/video.mp4 # Process video by full path
"""
import asyncio
import sys
import os
import glob
from pathlib import Path

# Add paths
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'moderation_service'))

# Import and ensure models
from model_registry import ensure_models

# Ensure required models are available
REQUIRED_MODELS = ['yolov8n', 'whisper', 'detoxify', 'paddleocr', 'ultralytics', 'torch']
print("Checking required models...")
if not ensure_models(REQUIRED_MODELS, verbose=True):
    print("⚠ Some models not available, video moderation may be limited")

# Sample videos directory
SAMPLE_VIDEOS_DIR = BASE_DIR / 'sample_videos'

# Supported video formats
VIDEO_EXTENSIONS = ['.mp4', '.webm', '.mov', '.avi', '.mkv', '.m4v', '.flv']


def find_videos(target=None):
    """Find videos to process."""
    videos = []

    if target:
        # Specific file provided
        if os.path.isabs(target):
            # Full path
            if os.path.exists(target):
                videos.append(target)
            else:
                print(f"❌ Video not found: {target}")
        else:
            # Relative path - check sample_videos directory
            video_path = SAMPLE_VIDEOS_DIR / target
            if video_path.exists():
                videos.append(str(video_path))
            else:
                print(f"❌ Video not found: {video_path}")
    else:
        # Find all videos in sample_videos directory
        for ext in VIDEO_EXTENSIONS:
            videos.extend(glob.glob(str(SAMPLE_VIDEOS_DIR / f"*{ext}")))
            videos.extend(glob.glob(str(SAMPLE_VIDEOS_DIR / f"*{ext.upper()}")))

    return sorted(set(videos))


async def process_video(video_path: str):
    """Process a single video file."""
    from moderation_service.app.services.video_moderation_pipeline import VideoModerationPipeline

    print("\n" + "=" * 70)
    print(f"   PROCESSING: {os.path.basename(video_path)}")
    print("=" * 70)

    # Get file info
    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    print(f"\n📁 File: {video_path}")
    print(f"📦 Size: {file_size_mb:.2f} MB")

    # Initialize pipeline
    print("\n🔧 Initializing moderation pipeline...")
    pipeline = VideoModerationPipeline(
        batch_size=8,
        audio_chunks=10,
        use_batch_coordinator=False  # Use sync mode for reliability
    )

    print("🎬 Running video moderation...")

    try:
        # Process video
        result = pipeline.moderate_video(video_path)

        # Display results
        print("\n" + "━" * 70)
        print("MODERATION RESULT")
        print("━" * 70)

        if not result.success:
            print(f"❌ Moderation failed: {result.error}")
            return result

        print(f"\n📋 Decision: {result.decision.upper()}")
        print(f"⚠️  Risk Level: {result.risk_level}")
        print(f"📊 Global Score: {result.global_score:.2f} (1.0 = safe)")
        print(f"🎞️  Frames Analyzed: {result.frames_analyzed}")
        print(f"⏱️  Processing Time: {result.processing_time_ms:.0f}ms ({result.processing_time_ms/1000:.1f}s)")

        print(f"\n📈 Category Scores:")
        for category, score in result.category_scores.items():
            bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
            status = "🔴" if score > 0.5 else "🟡" if score > 0.3 else "🟢"
            print(f"   {status} {category:15} [{bar}] {score:.2f}")

        if result.flags:
            print(f"\n🚩 Flags: {', '.join(result.flags)}")

        if result.reasons:
            print(f"\n📝 Reasons:")
            for reason in result.reasons[:5]:
                print(f"   • {reason}")

        # Audio transcription
        if hasattr(result, 'audio_transcription') and result.audio_transcription:
            print(f"\n🔊 Audio Transcription Preview:")
            preview = result.audio_transcription[:500]
            if len(result.audio_transcription) > 500:
                preview += "..."
            print(f"   {preview}")

        return result

    except Exception as e:
        import traceback
        print(f"\n❌ Error processing video: {e}")
        traceback.print_exc()
        return None


async def main():
    """Main entry point."""
    print("=" * 70)
    print("   OFFLINE VIDEO MODERATION TEST")
    print("=" * 70)

    # Get target video from command line
    target = sys.argv[1] if len(sys.argv) > 1 else None

    # Find videos
    videos = find_videos(target)

    if not videos:
        print(f"\n⚠️  No videos found!")
        print(f"\n📂 Please add video files to: {SAMPLE_VIDEOS_DIR}")
        print(f"\n   Supported formats: {', '.join(VIDEO_EXTENSIONS)}")
        print(f"\n   Example:")
        print(f"      cp /path/to/video.mp4 {SAMPLE_VIDEOS_DIR}/")
        print(f"      python test_offline_video.py video.mp4")
        return

    print(f"\n📹 Found {len(videos)} video(s) to process:")
    for v in videos:
        print(f"   • {os.path.basename(v)}")

    # Process each video
    results = []
    for video_path in videos:
        result = await process_video(video_path)
        results.append({
            'video': os.path.basename(video_path),
            'result': result
        })

    # Summary
    if len(results) > 1:
        print("\n" + "=" * 70)
        print("   SUMMARY")
        print("=" * 70)

        for r in results:
            if r['result'] and r['result'].success:
                decision = r['result'].decision.upper()
                icon = "🚫" if decision == "BLOCK" else "⚠️" if decision == "REVIEW" else "✅"
                print(f"   {icon} {r['video']}: {decision}")
            else:
                print(f"   ❌ {r['video']}: FAILED")

    print("\n" + "=" * 70)
    print("   TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

