#!/usr/bin/env python3
"""Test video moderation pipeline imports"""
import sys
sys.path.insert(0, '.')

print('Testing video moderation pipeline imports...')
print()

# Test individual components
try:
    from app.services.video.separate_video_audio import VideoAudioSeparator
    print('✅ VideoAudioSeparator imported')
except Exception as e:
    print(f'❌ VideoAudioSeparator failed: {e}')

try:
    from app.services.video.extract_video_frames import VideoFrameExtractor
    print('✅ VideoFrameExtractor imported')
except Exception as e:
    print(f'❌ VideoFrameExtractor failed: {e}')

try:
    from app.services.video.video_frame_processor import VideoFrameProcessor
    print('✅ VideoFrameProcessor imported')
except Exception as e:
    print(f'❌ VideoFrameProcessor failed: {e}')

try:
    from app.services.audio.audio_processor import AudioProcessor
    print('✅ AudioProcessor imported')
except Exception as e:
    print(f'❌ AudioProcessor failed: {e}')

# Test main pipeline
try:
    from app.services.video_moderation_pipeline import VideoModerationPipeline
    print('✅ VideoModerationPipeline imported')
except Exception as e:
    print(f'❌ VideoModerationPipeline failed: {e}')

print()
print('Import test complete!')

