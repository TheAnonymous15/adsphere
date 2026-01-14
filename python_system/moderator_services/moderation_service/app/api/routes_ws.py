"""
routes_ws.py – async websocket moderation dispatcher

Supports:
 - async job scheduling & result streaming
 - partial updates streamed when workers append
 - clean cancel/disconnect management
 - AI-powered category search
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import time

from app.services.lifecycle import coordinator, cache

# Import search service
try:
    from app.services.search_assisatnt.search_service import SearchService
    search_service = SearchService()
    SEARCH_AVAILABLE = True
except ImportError:
    search_service = None
    SEARCH_AVAILABLE = False

router = APIRouter()


@router.websocket("/moderate")
async def ws_moderate(websocket: WebSocket):
    await websocket.accept()

    try:
        # ==========================================================
        # Receive request:
        # {
        #     "job_id": "...",
        #     "asset_base64": "...",
        # }
        # ==========================================================
        raw_msg = await websocket.receive_text()
        msg = json.loads(raw_msg)

        job_id = msg["job_id"]
        asset_bytes = msg["asset_base64"].encode("utf-8")  # example

        # First check cache hit
        cached = await cache.get(cache.hash_asset(asset_bytes))
        if cached:
            await websocket.send_json({
                "job_id": job_id,
                "cached": True,
                "final": True,
                "result": cached
            })
            await websocket.close()
            return

        # ==========================================================
        # schedule async task into batch coordinator
        # ==========================================================
        await coordinator.schedule(job_id, asset_bytes)

        # ==========================================================
        # stream partials until full task result available
        # ==========================================================
        fut = coordinator._pending[job_id]

        # we poll until complete
        while not fut.done():
            await asyncio.sleep(0.01)

            partial = getattr(fut, "_partial", None)
            if partial:
                await websocket.send_json({
                    "job_id": job_id,
                    "partial": True,
                    "data": partial
                })

        # FUTURE COMPLETED → full result ready
        full = fut.result()

        # ==========================================================
        # write to cache
        # ==========================================================
        await cache.put(cache.hash_asset(asset_bytes), full)

        # ==========================================================
        # send final response + close ws
        # ==========================================================
        await websocket.send_json({
            "job_id": job_id,
            "final": True,
            "data": full,
        })

        await websocket.close()

    except WebSocketDisconnect:
        print("Client disconnected")
        return

    except asyncio.CancelledError:
        print("WS moderation cancelled", job_id)
        return

    except Exception as e:
        await websocket.send_json({
            "error": str(e),
            "fatal": True
        })
        await websocket.close()


@router.websocket("/search")
async def ws_search(websocket: WebSocket):
    """
    WebSocket endpoint for real-time AI-powered category search.

    Supports continuous search as user types (debounced on client).

    Request format:
    {
        "action": "search",  // or "quick"
        "query": "hungry",
        "top_k": 5,
        "threshold": 0.25,
        "categories": [...]  // optional custom categories
    }

    Response format:
    {
        "success": true,
        "query": "hungry",
        "results": [{"slug": "food", "name": "Food", "score": 0.95, "match_type": "semantic"}],
        "count": 1,
        "processing_time_ms": 12.5
    }
    """
    await websocket.accept()

    if not SEARCH_AVAILABLE:
        await websocket.send_json({
            "success": False,
            "error": "Search service not available"
        })
        await websocket.close()
        return

    try:
        while True:
            # Receive search request
            raw_msg = await websocket.receive_text()

            try:
                msg = json.loads(raw_msg)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "success": False,
                    "error": "Invalid JSON"
                })
                continue

            action = msg.get("action", "search")
            query = msg.get("query", "").strip()

            # Handle ping/pong for keepalive
            if action == "ping":
                await websocket.send_json({"action": "pong"})
                continue

            # Handle close request
            if action == "close":
                await websocket.close()
                return

            # Validate query
            if not query:
                await websocket.send_json({
                    "success": True,
                    "query": "",
                    "results": [],
                    "count": 0
                })
                continue

            start_time = time.time()

            try:
                # Set custom categories if provided
                if msg.get("categories"):
                    search_service.set_categories(msg["categories"])

                # Perform search
                top_k = msg.get("top_k", 5 if action == "search" else 3)
                threshold = msg.get("threshold", 0.25)

                result = search_service.search(query, top_k, threshold)
                result["processing_time_ms"] = round((time.time() - start_time) * 1000, 2)

                await websocket.send_json(result)

            except Exception as e:
                await websocket.send_json({
                    "success": False,
                    "error": str(e),
                    "query": query,
                    "results": [],
                    "count": 0
                })

    except WebSocketDisconnect:
        print("Search client disconnected")
        return

    except asyncio.CancelledError:
        print("Search WebSocket cancelled")
        return

    except Exception as e:
        try:
            await websocket.send_json({
                "error": str(e),
                "fatal": True
            })
        except:
            pass
        await websocket.close()

