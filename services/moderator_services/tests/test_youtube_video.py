#!/usr/bin/env python3
"""
Test YouTube Video Moderation
Tests the full pipeline on a YouTube video
"""
import asyncio
import sys
import os
from pathlib import Path

# Add paths
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'moderation_service'))

# Import and ensure models
from model_registry import ensure_models

# Ensure required models are available
REQUIRED_MODELS = ['yolov8n', 'whisper', 'detoxify', 'paddleocr', 'torch']
print("Checking required models...")
if not ensure_models(REQUIRED_MODELS, verbose=True):
    print("⚠ Some models not available, video moderation may be limited")

async def test_youtube_video():
    """Test YouTube video moderation"""

    url = "https://youtu.be/qkoH_bqzkzY"

    print("=" * 70)
    print("   YOUTUBE VIDEO MODERATION TEST")
    print("=" * 70)
    print(f"\n🔗 URL: {url}")
    print(f"📏 Max Duration: 300 seconds (5 minutes)")
    print()

    # Step 1: Check video info first
    print("━" * 70)
    print("STEP 1: Getting video info...")
    print("━" * 70)

    from app.services.video.youtube_processor import YouTubeProcessor, check_youtube_video

    info = await check_youtube_video(url)

    if not info.get('valid'):
        print(f"❌ Invalid video: {info.get('error')}")
        return

    print(f"✅ Video ID: {info.get('video_id')}")
    print(f"📺 Title: {info.get('title')}")
    print(f"👤 Channel: {info.get('channel')}")
    print(f"⏱️  Duration: {info.get('duration', 0):.0f} seconds ({info.get('duration', 0)/60:.1f} minutes)")
    print(f"👁️  Views: {info.get('view_count', 0):,}")
    print(f"🔴 Live: {info.get('is_live', False)}")
    print(f"🔞 Age Restricted: {info.get('is_age_restricted', False)}")

    if info.get('warnings'):
        print(f"⚠️  Warnings: {', '.join(info['warnings'])}")

    print(f"\n{'✅ Can Process' if info.get('can_process') else '❌ Cannot Process'}")

    if not info.get('can_process') and info.get('is_live'):
        print("Cannot process live streams")
        return

    # Step 2: Download video
    print("\n" + "━" * 70)
    print("STEP 2: Downloading video...")
    print("━" * 70)

    processor = YouTubeProcessor(max_duration=300)
    download_result = await processor.download_video(url)

    if not download_result.success:
        print(f"❌ Download failed: {download_result.error}")
        return

    print(f"✅ Downloaded in {download_result.download_time_ms:.0f}ms")
    print(f"📁 Video: {download_result.video_path}")
    print(f"🔊 Audio: {download_result.audio_path}")
    print(f"📂 Temp Dir: {download_result.temp_dir}")

    # Step 3: Run moderation pipeline
    print("\n" + "━" * 70)
    print("STEP 3: Running moderation pipeline...")
    print("━" * 70)

    try:
        from app.services.video_moderation_pipeline import VideoModerationPipeline

        pipeline = VideoModerationPipeline(
            batch_size=8,
            audio_chunks=10,
            use_batch_coordinator=False  # Use sync mode for debugging
        )

        print(f"   Using sync mode (not async) for debugging...")

        # Use sync method instead of async
        result = pipeline.moderate_video(download_result.video_path)

        print("\n" + "━" * 70)
        print("MODERATION RESULT")
        print("━" * 70)

        print(f"\n📋 Decision: {result.decision.upper()}")
        print(f"⚠️  Risk Level: {result.risk_level}")
        print(f"📊 Global Score: {result.global_score:.2f} (1.0 = safe)")
        print(f"🎞️  Frames Analyzed: {result.frames_analyzed}")
        print(f"⏱️  Processing Time: {result.processing_time_ms:.0f}ms")

        print(f"\n📈 Category Scores:")
        for category, score in result.category_scores.items():
            bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
            print(f"   {category:15} [{bar}] {score:.2f}")

        if result.flags:
            print(f"\n🚩 Flags: {', '.join(result.flags)}")

        if result.reasons:
            print(f"\n📝 Reasons:")
            for reason in result.reasons[:5]:
                print(f"   • {reason}")

        print(f"\n🔊 Audio Transcription Preview:")
        if result.audio_transcription:
            preview = result.audio_transcription[:500]
            if len(result.audio_transcription) > 500:
                preview += "..."
            print(f"   {preview}")
        else:
            print("   (No transcription available)")

    except Exception as e:
        import traceback
        print(f"❌ Moderation failed: {e}")
        traceback.print_exc()

    finally:
        # Cleanup
        print("\n" + "━" * 70)
        print("CLEANUP")
        print("━" * 70)
        processor.cleanup(download_result)
        print("✅ Temporary files cleaned up")

    print("\n" + "=" * 70)
    print("   TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_youtube_video())

