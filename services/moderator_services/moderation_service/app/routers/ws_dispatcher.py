"""
WebSocket dispatcher for multimodal moderation.
Streams partial reasoning, OCR, caption + NSFW/violence signals.

Features:
- async binary/protobuf WebSocket frames
- Pydantic JSON payload fallback
- lock-free queue backpressure guard
- session-aware rate limiting
- streaming heartbeat maintain TCP flow
- metrics instrumentation
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.lifecycle import coordinator, queue
from app.services.backpressure import BackpressureGuard, BackpressureError
from app.services.rate_limit import RateLimiter
from app.metrics.metrics import (
    tasks_dispatched_counter,
    rate_limited_sessions_counter,
    queue_overflow_counter,
    active_ws_connections,
    partial_chunks_counter,
    binary_frames_counter,
)

from app.proto.moderation_pb2 import ModerationFrame  # protoc generated

import orjson


router = APIRouter()

# shared guards
rate_limiter = RateLimiter(limit=25, per_seconds=1.0)
backpressure = BackpressureGuard(queue, pressure_limit=10_000)


# ------------------------------
# encoding utils
# ------------------------------

def encode_json(obj) -> bytes:
    """
    Fast Pydantic / dict encoder.
    Ensures UTF-8 serialized text -> bytes.
    """
    try:
        # obj is pydantic model
        return orjson.dumps(obj.model_dump())
    except AttributeError:
        # assume dict-like object
        return orjson.dumps(obj)


def encode_protobuf(task_id: str, seq: int, final: bool, payload: bytes) -> bytes:
    """
    Construct ModerationFrame protobuf message.
    payload MUST already be binary-safe.
    """
    frame = ModerationFrame(
        task_id=task_id,
        sequence=seq,
        final=final,
        payload=payload,
    )
    # returns raw binary
    return frame.SerializeToString()


# ------------------------------
# MAIN WS ENTRYPOINT
# ------------------------------

@router.websocket("/ws/moderate")
async def ws_moderate(ws: WebSocket):
    """
    Primary async WS dispatcher for multimodal moderation.
    """

    await ws.accept()
    active_ws_connections.inc()

    session_id = ws.headers.get("x-session-id", "anon")
    seq = 0

    try:

        async for msg in ws.iter_text():

            # ----------------------------------------------
            # 1. Rate limit per session id
            # ----------------------------------------------
            if not rate_limiter.allow(session_id):
                rate_limited_sessions_counter.inc()
                await ws.send_text('{"error":"rate_limited"}')
                continue

            # ----------------------------------------------
            # 2. Queue backpressure guard
            # ----------------------------------------------
            try:
                await backpressure.check()
            except BackpressureError:
                queue_overflow_counter.inc()
                await ws.send_text('{"error":"queue_overflow"}')
                continue

            # ----------------------------------------------
            # 3. Parse moderation request
            # ----------------------------------------------
            try:
                task = coordinator.parse_request(msg)
            except Exception:
                await ws.send_text('{"error":"bad_request"}')
                continue

            tasks_dispatched_counter.inc()

            # ----------------------------------------------
            # 4. Scheduling returns async generator
            # ----------------------------------------------
            stream = await coordinator.schedule(task)

            # ----------------------------------------------
            # 5. streaming loop
            # ----------------------------------------------
            async for chunk in stream:
                seq += 1
                final = getattr(chunk, "final", False)

                # detect type – bytes or structured object
                if isinstance(chunk, bytes):
                    binary_frames_counter.inc()
                    payload = chunk  # already bytes
                else:
                    payload = encode_json(chunk)

                # encode into protobuf WS frame
                message = encode_protobuf(task.id, seq, final, payload)

                partial_chunks_counter.inc()

                try:
                    # always send protobuf frames as WS binary frames
                    await ws.send_bytes(message)
                except RuntimeError:
                    # socket closed or backpressure write failure
                    break

                # --- heartbeat separator ---
                # keeps TCP moving + avoids buffer stall
                try:
                    await ws.send_text("·")
                except RuntimeError:
                    break

    except WebSocketDisconnect:
        # graceful disconnect
        pass

    finally:
        active_ws_connections.dec()
        await ws.close()
