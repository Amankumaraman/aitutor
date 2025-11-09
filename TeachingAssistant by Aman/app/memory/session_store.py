# app/memory/session_store.py
import os
import json
from dotenv import load_dotenv

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

import aioredis

_redis = None

async def init_redis():
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis

async def push_turn(session_id: str, speaker: str, text: str, max_turns: int = 30):
    r = await init_redis()
    key = f"session:{session_id}:turns"
    await r.rpush(key, json.dumps({"speaker": speaker, "text": text}))
    await r.ltrim(key, -max_turns, -1)

async def get_recent(session_id: str, n: int = 10):
    r = await init_redis()
    key = f"session:{session_id}:turns"
    items = await r.lrange(key, -n, -1)
    return [json.loads(i) for i in items]
