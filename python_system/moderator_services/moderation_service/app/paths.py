"""
Path Utilities for AdSphere Moderation Service
===============================================

This module provides centralized path utilities for all moderation service modules.
Import this module to get correctly set up paths for model_registry and other imports.

Usage:
    from paths import setup_paths, MODERATOR_SERVICES_DIR
    setup_paths()  # Call once to set up sys.path

    # Now import model_registry
    from model_registry import ModelStore, ensure_models
"""

import sys
from pathlib import Path

# Calculate the base path - this file is at: moderator_services/moderation_service/app/paths.py
_THIS_FILE = Path(__file__).resolve()
APP_DIR = _THIS_FILE.parent
MODERATION_SERVICE_DIR = APP_DIR.parent
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent
SERVICES_DIR = APP_DIR / 'services'

# Subdirectories
TEXT_DIR = SERVICES_DIR / 'text'
IMAGES_DIR = SERVICES_DIR / 'images'
VIDEO_DIR = SERVICES_DIR / 'video'
AUDIO_DIR = SERVICES_DIR / 'audio'
SEARCH_DIR = SERVICES_DIR / 'search_assisatnt'

# Other important directories
MODELS_DIR = MODERATION_SERVICE_DIR / 'models_weights'
CACHE_DIR = MODERATOR_SERVICES_DIR / 'cache'
SAMPLE_IMAGES_DIR = MODERATOR_SERVICES_DIR / 'sample_images'
SAMPLE_VIDEOS_DIR = MODERATOR_SERVICES_DIR / 'sample_videos'

# Paths that need to be added to sys.path
_PATHS_TO_ADD = [
    str(MODERATOR_SERVICES_DIR),  # For model_registry.py
    str(MODERATION_SERVICE_DIR),  # For moderation_service modules
    str(APP_DIR),                  # For app modules
]

_paths_initialized = False


def setup_paths():
    """
    Add necessary directories to Python path.
    This is idempotent - calling multiple times has no additional effect.
    """
    global _paths_initialized
    if _paths_initialized:
        return

    for path in _PATHS_TO_ADD:
        if path not in sys.path:
            sys.path.insert(0, path)

    _paths_initialized = True


def get_relative_to_moderator_services(*parts):
    """Get a path relative to the moderator_services directory."""
    return MODERATOR_SERVICES_DIR.joinpath(*parts)


def get_relative_to_app(*parts):
    """Get a path relative to the app directory."""
    return APP_DIR.joinpath(*parts)


# Auto-setup when imported
setup_paths()


# Convenience imports - after path setup
try:
    from model_registry import ModelStore, ensure_models, get_model_path, check_models
    MODEL_REGISTRY_AVAILABLE = True
except ImportError:
    MODEL_REGISTRY_AVAILABLE = False
    ModelStore = None
    def ensure_models(models, verbose=False): return True
    def get_model_path(model_name): return None
    def check_models(models=None): return {}


__all__ = [
    # Path setup
    'setup_paths',

    # Directories
    'MODERATOR_SERVICES_DIR',
    'MODERATION_SERVICE_DIR',
    'APP_DIR',
    'SERVICES_DIR',
    'TEXT_DIR',
    'IMAGES_DIR',
    'VIDEO_DIR',
    'AUDIO_DIR',
    'SEARCH_DIR',
    'MODELS_DIR',
    'CACHE_DIR',
    'SAMPLE_IMAGES_DIR',
    'SAMPLE_VIDEOS_DIR',

    # Utilities
    'get_relative_to_moderator_services',
    'get_relative_to_app',

    # Model registry
    'MODEL_REGISTRY_AVAILABLE',
    'ModelStore',
    'ensure_models',
    'get_model_path',
    'check_models',
]

