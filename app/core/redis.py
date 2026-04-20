import json
from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import settings


redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def cache_json(key: str, value: Any, ttl: int) -> None:
    await redis_client.setex(key, ttl, json.dumps(value, ensure_ascii=False))


async def get_cached_json(key: str) -> Optional[Any]:
    cached = await redis_client.get(key)
    if not cached:
        return None
    return json.loads(cached)
