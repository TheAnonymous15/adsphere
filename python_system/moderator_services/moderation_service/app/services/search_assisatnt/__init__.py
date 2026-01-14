# Search Assistant Module
# AI-powered category matching using semantic similarity

import sys
from pathlib import Path

# Set up paths for model_registry import
# Path: search_assisatnt/__init__.py -> search_assisatnt -> services -> app -> moderation_service -> moderator_services
SEARCH_DIR = Path(__file__).parent.resolve()
SERVICES_DIR = SEARCH_DIR.parent.resolve()
APP_DIR = SERVICES_DIR.parent.resolve()
MODERATION_SERVICE_DIR = APP_DIR.parent.resolve()
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent.resolve()

for _path in [str(MODERATOR_SERVICES_DIR), str(MODERATION_SERVICE_DIR), str(APP_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from .category_matcher import CategoryMatcher
from .search_service import SearchService

__all__ = ['CategoryMatcher', 'SearchService']

