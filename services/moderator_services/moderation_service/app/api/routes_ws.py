"""
routes_ws.py – async websocket moderation dispatcher

Supports:
 - async job scheduling & result streaming
 - partial updates streamed when workers append
 - clean cancel/disconnect management
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json

from app.services.lifecycle import coordinator, cache

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
