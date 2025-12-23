"""
Path Setup Helper for AdSphere Moderation Service
==================================================

This module sets up the Python path to allow importing model_registry
from any submodule within the moderation service.

Usage:
    # At the top of any .py file that needs model_registry:
    from path_setup import setup_paths
    setup_paths()

    # Now you can import model_registry
    from model_registry import ModelStore, ensure_models, get_model_path
"""

import sys
from pathlib import Path

# Calculate all important directories relative to this file
# This file is at: moderator_services/moderation_service/path_setup.py
THIS_DIR = Path(__file__).parent.resolve()
MODERATOR_SERVICES_DIR = THIS_DIR.parent.resolve()  # Contains model_registry.py
MODERATION_SERVICE_DIR = THIS_DIR  # moderation_service/
APP_DIR = THIS_DIR / "app"
SERVICES_DIR = APP_DIR / "services"


def setup_paths():
    """
    Add necessary directories to Python path.
    Call this at the top of any module that needs to import model_registry.
    """
    paths_to_add = [
        str(MODERATOR_SERVICES_DIR),  # For model_registry
        str(MODERATION_SERVICE_DIR),  # For moderation_service modules
        str(APP_DIR),                  # For app modules
    ]

    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)


def get_model_registry():
    """
    Get the model_registry module after setting up paths.

    Returns:
        module: The model_registry module
    """
    setup_paths()
    import model_registry
    return model_registry


def get_model_store():
    """
    Get an initialized ModelStore instance.

    Returns:
        ModelStore: An instance of the model store
    """
    registry = get_model_registry()
    return registry.ModelStore()


# Directory exports
PATHS = {
    'moderator_services': MODERATOR_SERVICES_DIR,
    'moderation_service': MODERATION_SERVICE_DIR,
    'app': APP_DIR,
    'services': SERVICES_DIR,
    'models_weights': MODERATION_SERVICE_DIR / 'models_weights',
    'cache': MODERATOR_SERVICES_DIR / 'cache',
    'sample_images': MODERATOR_SERVICES_DIR / 'sample_images',
    'sample_videos': MODERATOR_SERVICES_DIR / 'sample_videos',
}


# Auto-setup paths when this module is imported
setup_paths()

