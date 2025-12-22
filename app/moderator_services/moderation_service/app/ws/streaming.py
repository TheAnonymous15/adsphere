"""
app/ws/streaming.py
incremental serialization for async streaming
"""

from typing import AsyncIterator, Union

import orjson
from pydantic import BaseModel
from google.protobuf.message import Message as ProtoMessage


# ---- JSON encode using orjson for speed ----
def encode_json(obj: Union[dict, BaseModel]) -> bytes:
    if isinstance(obj, BaseModel):
        # use .model_dump() not dict()
        return orjson.dumps(obj.model_dump())

    # dict / primitive
    return orjson.dumps(obj)


# ---- protobuf length-prefixed binary frame encoding ----
def encode_protobuf(msg: ProtoMessage) -> bytes:
    raw = msg.SerializeToString()
    size = len(raw).to_bytes(4, byteorder="big")  # 4-byte prefix

    return size + raw


# ---- switch encoder for incoming chunks ----
def encode_frame(chunk) -> bytes:
    """
    Input chunk types:
    - bytes                -> returned directly
    - dict / BaseModel     -> encoded as UTF-8 JSON
    - protobuf msg         -> binary proto frame

    Returned as raw bytes. WS sender decides send_bytes/send_text.
    """

    if isinstance(chunk, bytes):
        return chunk

    if isinstance(chunk, BaseModel):
        return encode_json(chunk)

    if isinstance(chunk, dict):
        return encode_json(chunk)

    if isinstance(chunk, ProtoMessage):
        return encode_protobuf(chunk)

    raise TypeError(f"unsupported chunk type: {type(chunk)}")


# ---- generator for ws dispatcher ----
async def stream_frames(chunks: AsyncIterator) -> AsyncIterator[bytes]:
    """
    Converts async chunk stream into serialized byte frames.
    """
    async for chunk in chunks:
        yield encode_frame(chunk)
