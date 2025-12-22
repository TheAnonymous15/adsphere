# Test Fixtures for Moderation System

This directory contains sample content for testing the moderation system.

## Directory Structure

```
fixtures/
├── text/
│   ├── safe/          - Safe content examples
│   ├── unsafe/        - Unsafe content examples (various violations)
│   └── borderline/    - Edge cases
├── images/
│   ├── safe/          - Safe images
│   ├── nsfw/          - NSFW images (for testing)
│   ├── violence/      - Violence imagery
│   └── weapons/       - Weapons imagery
└── videos/
    ├── safe/          - Safe videos
    ├── nsfw/          - NSFW videos
    ├── violence/      - Violence videos
    └── weapons/       - Weapons videos
```

## Usage

```python
import json

# Load text fixtures
with open('fixtures/text/unsafe/violence.json') as f:
    violence_samples = json.load(f)

# Use in tests
for sample in violence_samples:
    result = moderate_text(sample['text'])
    assert result['decision'] == 'block'
```

## Adding New Fixtures

1. Place content in appropriate category folder
2. For text: use JSON format with metadata
3. For images/videos: use descriptive filenames
4. Update metadata files if needed

## Important Notes

⚠️ **NSFW Content**: This directory may contain explicit content for testing purposes only. Handle appropriately.

⚠️ **Security**: Do not commit real user data or copyrighted material.

⚠️ **Privacy**: All test content should be synthetic or publicly available.

