"""
AI Search API
Communicates with the moderation service's search assistant via WebSocket
Falls back to REST API if WebSocket unavailable
Converted from PHP to Python
"""

from fastapi import APIRouter, Query
from pathlib import Path
from typing import Optional
import httpx
import json
import os
import sqlite3
import asyncio
import websockets
import time

router = APIRouter()

# Configuration
SEARCH_SERVICE_HOST = os.getenv('SEARCH_SERVICE_HOST', 'localhost')
SEARCH_SERVICE_PORT = os.getenv('SEARCH_SERVICE_PORT', '8002')
SEARCH_SERVICE_URL = f"http://{SEARCH_SERVICE_HOST}:{SEARCH_SERVICE_PORT}"
SEARCH_WS_URL = f"ws://{SEARCH_SERVICE_HOST}:{SEARCH_SERVICE_PORT}/ws/search"
SEARCH_TIMEOUT = 5  # seconds

# Keyword mappings for fallback
KEYWORD_MAP = {
    'food': ['eat', 'eating', 'hungry', 'meal', 'restaurant', 'cook', 'cooking',
             'breakfast', 'lunch', 'dinner', 'snack', 'drink', 'grocery', 'kitchen',
             'chef', 'delicious', 'tasty', 'cuisine', 'dining', 'cafe', 'pizza',
             'burger', 'coffee', 'tea', 'bakery'],
    'electronics': ['tv', 'television', 'radio', 'phone', 'smartphone', 'laptop',
                   'computer', 'pc', 'tablet', 'gadget', 'device', 'tech', 'technology',
                   'gaming', 'console', 'headphone', 'speaker', 'camera', 'printer',
                   'monitor', 'keyboard', 'wifi', 'bluetooth', 'smart', 'digital'],
    'housing': ['house', 'home', 'apartment', 'flat', 'rent', 'rental', 'lease',
               'buy', 'sell', 'property', 'real estate', 'room', 'bedroom',
               'land', 'plot', 'building', 'condo', 'villa', 'mortgage', 'tenant'],
    'vehicles': ['car', 'vehicle', 'auto', 'automobile', 'truck', 'van', 'suv',
                'motorcycle', 'bike', 'bicycle', 'scooter', 'drive', 'driving',
                'fuel', 'petrol', 'diesel', 'engine', 'tire', 'wheel', 'transport'],
    'fashion': ['clothes', 'clothing', 'dress', 'shirt', 'pants', 'jeans', 'shoes',
               'jacket', 'coat', 'sweater', 'bag', 'handbag', 'watch', 'jewelry',
               'accessory', 'fashion', 'style', 'outfit', 'wear', 'designer'],
    'health': ['health', 'healthy', 'medical', 'medicine', 'doctor', 'hospital',
              'clinic', 'pharmacy', 'fitness', 'gym', 'workout', 'exercise',
              'wellness', 'beauty', 'skincare', 'makeup', 'spa', 'diet', 'nutrition'],
    'jobs': ['job', 'jobs', 'work', 'working', 'career', 'employment', 'hire',
            'hiring', 'recruit', 'resume', 'cv', 'interview', 'salary', 'wage',
            'office', 'remote', 'freelance', 'part-time', 'full-time', 'vacancy'],
    'services': ['service', 'repair', 'fix', 'install', 'maintenance', 'cleaning',
                'plumber', 'electrician', 'carpenter', 'painting', 'delivery',
                'catering', 'event', 'photography', 'consulting', 'legal', 'insurance'],
    'education': ['school', 'college', 'university', 'study', 'learn', 'learning',
                 'course', 'class', 'lesson', 'tutor', 'teacher', 'student', 'degree',
                 'training', 'workshop', 'online', 'book', 'exam', 'scholarship'],
    'travel': ['travel', 'trip', 'vacation', 'holiday', 'tour', 'tourism',
              'flight', 'airline', 'hotel', 'resort', 'booking', 'ticket',
              'beach', 'mountain', 'safari', 'adventure', 'destination', 'cruise'],
    'sports': ['sport', 'sports', 'football', 'soccer', 'basketball', 'tennis',
              'swimming', 'running', 'gym', 'fitness', 'workout', 'athlete',
              'team', 'match', 'game', 'league', 'tournament', 'cycling'],
    'entertainment': ['movie', 'film', 'cinema', 'music', 'concert', 'show', 'tv',
                     'streaming', 'netflix', 'game', 'gaming', 'party', 'club',
                     'dance', 'art', 'museum', 'festival', 'comedy', 'fun'],
    'furniture': ['furniture', 'sofa', 'couch', 'chair', 'table', 'desk', 'bed',
                 'mattress', 'wardrobe', 'cabinet', 'shelf', 'lamp', 'curtain',
                 'carpet', 'decor', 'decoration', 'interior', 'home'],
    'pets': ['pet', 'pets', 'dog', 'cat', 'puppy', 'kitten', 'bird', 'fish',
            'animal', 'vet', 'veterinary', 'pet food', 'adoption', 'grooming'],
    'books': ['book', 'books', 'reading', 'read', 'novel', 'fiction', 'magazine',
             'newspaper', 'library', 'ebook', 'audiobook', 'author', 'literature']
}


async def search_via_websocket(query: str, top_k: int = 5, threshold: float = 0.25, categories: list = None) -> Optional[dict]:
    """Search via WebSocket"""
    try:
        async with websockets.connect(SEARCH_WS_URL, timeout=3) as ws:
            request = {
                'action': 'search',
                'query': query,
                'top_k': top_k,
                'threshold': threshold
            }
            if categories:
                request['categories'] = categories

            await ws.send(json.dumps(request))
            response = await asyncio.wait_for(ws.recv(), timeout=SEARCH_TIMEOUT)
            return json.loads(response)
    except Exception:
        return None


async def quick_search_via_websocket(query: str, top_k: int = 3) -> Optional[dict]:
    """Quick search via WebSocket (just slugs)"""
    try:
        async with websockets.connect(SEARCH_WS_URL, timeout=3) as ws:
            await ws.send(json.dumps({
                'action': 'quick',
                'query': query,
                'top_k': top_k
            }))
            response = await asyncio.wait_for(ws.recv(), timeout=SEARCH_TIMEOUT)
            return json.loads(response)
    except Exception:
        return None


async def call_search_service_rest(endpoint: str, data: dict = None, method: str = 'GET') -> dict:
    """Make REST API request (fallback)"""
    url = f"{SEARCH_SERVICE_URL}/moderate/search/{endpoint.lstrip('/')}"

    try:
        async with httpx.AsyncClient(timeout=SEARCH_TIMEOUT) as client:
            if method == 'POST':
                response = await client.post(url, json=data)
            else:
                response = await client.get(url, params=data)

            if response.status_code != 200:
                return {'success': False, 'error': f'Service error: HTTP {response.status_code}'}

            return response.json()
    except Exception as e:
        return {'success': False, 'error': f'Service unavailable: {str(e)}'}


def fallback_keyword_match(query: str, categories: list) -> list:
    """Fallback keyword matching when service is unavailable"""
    query = query.lower().strip()
    if not query:
        return []

    query_words = query.split(' ')
    results = []

    for cat in categories:
        slug = (cat.get('slug') or cat.get('category_slug') or '').lower()
        name = (cat.get('name') or cat.get('category_name') or slug).lower()
        score = 0.0

        # Direct match with category name
        if query == slug or query == name:
            score = 1.0
        elif query in name or query in slug:
            score = 0.85
        elif name in query or slug in query:
            score = 0.8

        # Check keyword mappings
        if score < 0.7 and slug in KEYWORD_MAP:
            for keyword in KEYWORD_MAP[slug]:
                if query == keyword:
                    score = max(score, 0.95)
                    break
                elif keyword in query or query in keyword:
                    score = max(score, 0.75)
                # Check individual query words
                for word in query_words:
                    if len(word) >= 3 and (word in keyword or keyword in word):
                        score = max(score, 0.6)

        if score >= 0.25:
            results.append({
                'slug': slug,
                'name': cat.get('name') or cat.get('category_name') or slug.capitalize(),
                'score': round(score, 4),
                'match_type': 'keyword_fallback'
            })

    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:5]


def get_categories_from_db() -> list:
    """Get categories from database"""
    # Try multiple possible paths
    db_paths = [
        Path(__file__).parent.parent / 'database' / 'adsphere.db',
        Path(__file__).parent.parent.parent / 'shared' / 'database' / 'adsphere.db',
        Path(__file__).parent.parent.parent.parent / 'services' / 'shared' / 'database' / 'adsphere.db',
        Path(__file__).parent.parent.parent.parent / 'app' / 'adsphere.db',
    ]

    db_path = None
    for path in db_paths:
        if path.exists():
            db_path = path
            break

    if not db_path:
        return []

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT category_slug, category_name FROM categories ORDER BY category_name")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        return []


@router.get("/ai_search")
async def ai_search(
    action: str = Query("search", description="Action: search, match, quick, categories, health"),
    query: str = Query("", description="Search query"),
    limit: int = Query(5, ge=1, le=50, alias="limit"),
    top_k: int = Query(None, ge=1, le=50),
    threshold: float = Query(0.25, ge=0, le=1)
):
    """AI-powered category search API"""
    start_time = time.time()

    # Use top_k if provided, otherwise use limit
    top_k = top_k or limit

    if action in ['search', 'match']:
        if not query:
            return {
                "success": False,
                "error": "Query is required",
                "results": []
            }

        # Get categories from database
        categories = get_categories_from_db()

        # Prepare categories for API
        api_categories = [
            {'slug': cat.get('category_slug'), 'name': cat.get('category_name')}
            for cat in categories
        ]

        # Try WebSocket first
        result = await search_via_websocket(query, top_k, threshold, api_categories)

        if result and result.get('success'):
            processing_time = round((time.time() - start_time) * 1000, 2)
            return {
                "success": True,
                "query": query,
                "results": result.get('results', []),
                "count": result.get('count', 0),
                "processing_time_ms": result.get('processing_time_ms', processing_time),
                "model_type": result.get('model_type', 'semantic'),
                "source": "websocket"
            }

        # Fallback to REST API
        rest_result = await call_search_service_rest('match', {
            'query': query,
            'top_k': top_k,
            'threshold': threshold,
            'categories': api_categories
        }, 'POST')

        if rest_result.get('success'):
            processing_time = round((time.time() - start_time) * 1000, 2)
            return {
                "success": True,
                "query": query,
                "results": rest_result.get('results', []),
                "count": rest_result.get('count', 0),
                "processing_time_ms": rest_result.get('processing_time_ms', processing_time),
                "model_type": rest_result.get('model_type', 'semantic'),
                "source": "rest_api"
            }

        # Final fallback to keyword matching
        results = fallback_keyword_match(query, categories)
        processing_time = round((time.time() - start_time) * 1000, 2)

        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results),
            "processing_time_ms": processing_time,
            "model_type": "keyword_fallback",
            "source": "local_fallback",
            "service_error": rest_result.get('error')
        }

    elif action == 'quick':
        # Quick search - just return matching category slugs
        if not query:
            return {"success": True, "matches": []}

        categories = get_categories_from_db()
        top_k = top_k or 3

        # Try WebSocket first
        result = await quick_search_via_websocket(query, top_k)

        if result and result.get('success'):
            matches = [r.get('slug') for r in result.get('results', [])]
            return {
                "success": True,
                "matches": matches,
                "source": "websocket"
            }

        # Fallback to REST
        rest_result = await call_search_service_rest(
            f'quick/{query}',
            {'top_k': top_k},
            'GET'
        )

        if rest_result.get('success'):
            return {
                "success": True,
                "matches": rest_result.get('matches', []),
                "source": "rest_api"
            }

        # Fallback to local
        results = fallback_keyword_match(query, categories)
        matches = [r.get('slug') for r in results]

        return {
            "success": True,
            "matches": matches,
            "source": "local_fallback"
        }

    elif action == 'categories':
        # Return all categories
        categories = get_categories_from_db()
        return {
            "success": True,
            "categories": [
                {'slug': cat.get('category_slug'), 'name': cat.get('category_name')}
                for cat in categories
            ],
            "count": len(categories)
        }

    elif action == 'health':
        # Health check - try WebSocket first
        ws_connected = False
        try:
            async with websockets.connect(SEARCH_WS_URL, timeout=3) as ws:
                ws_connected = True
        except Exception:
            pass

        rest_result = await call_search_service_rest('health', {}, 'GET')

        return {
            "success": True,
            "api_status": "healthy",
            "websocket_available": ws_connected,
            "rest_available": rest_result.get('status') == 'healthy',
            "service_status": rest_result.get('status', 'unknown'),
            "model_loaded": rest_result.get('model_loaded', False)
        }

    else:
        return {
            "success": False,
            "error": f"Unknown action: {action}"
        }


# Additional POST endpoint for match (matches PHP behavior)
@router.post("/ai_search")
async def ai_search_post(
    action: str = Query("search"),
    query: str = Query(""),
    limit: int = Query(5),
    top_k: int = Query(None),
    threshold: float = Query(0.25)
):
    """POST endpoint for AI search (same as GET)"""
    return await ai_search(action, query, limit, top_k, threshold)
