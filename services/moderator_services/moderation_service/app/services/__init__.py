"""
Moderation Services Package
===========================

This package contains all moderation service implementations:

- text/        - Text moderation pipeline (toxicity, intent, context)
- images/      - Image moderation (security scan, OCR, NSFW, weapons)
- video/       - Video moderation (frame extraction, processing)
- audio/       - Audio moderation (speech-to-text, analysis)
- search_assisatnt/ - AI search assistance for category matching

Path Setup:
-----------
This package automatically sets up paths so model_registry can be imported.
"""

import sys
from pathlib import Path

# Set up paths for model_registry import
# This file is at: moderator_services/moderation_service/app/services/__init__.py
SERVICES_DIR = Path(__file__).parent.resolve()
APP_DIR = SERVICES_DIR.parent.resolve()
MODERATION_SERVICE_DIR = APP_DIR.parent.resolve()
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent.resolve()

# Add to path if not already present
_paths_to_add = [
    str(MODERATOR_SERVICES_DIR),
    str(MODERATION_SERVICE_DIR),
    str(APP_DIR),
    str(SERVICES_DIR),
]

for _path in _paths_to_add:
    if _path not in sys.path:
        sys.path.insert(0, _path)

# Import model_registry convenience functions
try:
    from model_registry import (
        ModelStore,
        ensure_models,
        get_model_path,
        check_models
    )
    MODEL_REGISTRY_AVAILABLE = True
except ImportError as e:
    MODEL_REGISTRY_AVAILABLE = False
    # Provide fallback functions
    def ensure_models(models, verbose=False):
        return True
    def get_model_path(model_name):
        return None
    def check_models(models=None):
        return {}
    ModelStore = None

__all__ = [
    'ModelStore',
    'ensure_models',
    'get_model_path',
    'check_models',
    'MODEL_REGISTRY_AVAILABLE',
    'SERVICES_DIR',
    'APP_DIR',
    'MODERATION_SERVICE_DIR',
    'MODERATOR_SERVICES_DIR'
]

