"""
AdSphere Moderation Service App Package
=======================================

This package contains the FastAPI application and all moderation services.

Path Setup:
-----------
This __init__.py automatically sets up Python paths so that model_registry
can be imported from any submodule.

Structure:
----------
app/
├── api/          - FastAPI routes
├── core/         - Core utilities (decision engine, auth, rate limiting)
├── infra/        - Infrastructure (queue client)
├── models/       - Pydantic schemas
├── proto/        - gRPC protocol buffers
├── routers/      - API routers
├── services/     - Moderation services (text, image, video, audio, search)
├── utils/        - Utility functions (logging, metrics)
├── workers/      - Background workers
└── ws/           - WebSocket handlers
"""

import sys
from pathlib import Path

# Calculate directory paths
# This file is at: moderator_services/moderation_service/app/__init__.py
APP_DIR = Path(__file__).parent.resolve()
MODERATION_SERVICE_DIR = APP_DIR.parent.resolve()
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent.resolve()

# Add paths to Python path for model_registry and other imports
_paths_to_add = [
    str(MODERATOR_SERVICES_DIR),  # For model_registry.py
    str(MODERATION_SERVICE_DIR),  # For moderation_service modules
    str(APP_DIR),                  # For app modules
]

for _path in _paths_to_add:
    if _path not in sys.path:
        sys.path.insert(0, _path)

# Now model_registry can be imported from anywhere
try:
    import model_registry
    MODEL_REGISTRY_AVAILABLE = True
except ImportError:
    MODEL_REGISTRY_AVAILABLE = False

# Export important paths
__all__ = [
    'APP_DIR',
    'MODERATION_SERVICE_DIR',
    'MODERATOR_SERVICES_DIR',
    'MODEL_REGISTRY_AVAILABLE'
]

