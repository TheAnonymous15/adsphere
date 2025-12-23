"""
AdSphere Moderation Services Package
====================================

This package provides AI/ML-powered content moderation for:
- Text analysis (toxicity, hate speech, intent classification)
- Image moderation (NSFW, weapons, violence, OCR)
- Video moderation (frame extraction, audio analysis)
- Search assistance (semantic category matching)

The model_registry module in this directory serves as the central
model store that all submodules should use.
"""

import sys
from pathlib import Path

# Set up the path so model_registry can be imported from anywhere
MODERATOR_SERVICES_DIR = Path(__file__).parent.resolve()
MODERATION_SERVICE_DIR = MODERATOR_SERVICES_DIR / "moderation_service"
APP_DIR = MODERATION_SERVICE_DIR / "app"
SERVICES_DIR = APP_DIR / "services"

# Add this directory to Python path for model_registry imports
if str(MODERATOR_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(MODERATOR_SERVICES_DIR))

# Make model_registry importable
from . import model_registry

__all__ = [
    'model_registry',
    'MODERATOR_SERVICES_DIR',
    'MODERATION_SERVICE_DIR',
    'APP_DIR',
    'SERVICES_DIR'
]

__version__ = "1.0.0"

