import asyncio
import json
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)


class AIClient:
    def __init__(self) -> None:
        self.base_headers = {
            "Authorization": f"Bearer {settings.API_KEY}",
            "Content-Type": "application/json",
        }

    async def _post_json(
        self,
        *,
        url: str,
        payload: dict[str, Any],
        timeout: float = 180.0,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=self.base_headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def analyze_product(self, *, prompt: str, image_data_url: str) -> str:
        payload = {
            "model": settings.MULTIMODAL_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一名资深电商分析师，请从商品视觉与文本中提炼用户需求、卖点与营销方向。",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                        {"type": "text", "text": prompt},
                    ],
                },
            ],
            "temperature": 0.5,
        }
        data = await self._post_json(url=settings.BASE_URL, payload=payload)
        return data["choices"][0]["message"]["content"]

    async def generate_strategy(self, *, prompt: str) -> dict[str, Any]:
        payload = {
            "model": settings.DEEPSEEK_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一名资深电商策略师，只返回合法 JSON，输出必须使用简体中文。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.6,
            "response_format": {"type": "json_object"},
        }
        data = await self._post_json(url=settings.BASE_URL, payload=payload, timeout=120.0)
        return json.loads(data["choices"][0]["message"]["content"])

    async def generate_image(self, *, prompt: str, image_data_url: str, size: str) -> str:
        payload = {
            "model": settings.SEEDREAM_IMAGE_MODEL,
            "prompt": prompt,
            "image": image_data_url,
            "response_format": "url",
            "size": size,
            "stream": False,
            "watermark": False,
            "sequential_image_generation": "disabled",
        }
        data = await self._post_json(
            url=settings.SEEDREAM_IMAGE_URL,
            payload=payload,
            timeout=180.0,
        )
        return data["data"][0]["url"]

    async def generate_images(
        self,
        *,
        specs: list[dict[str, Any]],
        image_data_url: str,
        size: str,
    ) -> list[dict[str, Any]]:
        semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_IMAGE_GEN)
        results: list[dict[str, Any]] = [None] * len(specs)

        async def worker(index: int, spec: dict[str, Any]) -> None:
            async with semaphore:
                prompt = spec.get("prompt", "").strip()
                if not prompt:
                    results[index] = {
                        "position": spec.get("position", index + 1),
                        "prompt": "",
                        "url": "",
                        "error": "prompt is empty",
                    }
                    return
                try:
                    url = await self.generate_image(
                        prompt=prompt,
                        image_data_url=image_data_url,
                        size=size,
                    )
                    results[index] = {
                        "position": spec.get("position", index + 1),
                        "prompt": prompt,
                        "url": url,
                    }
                except Exception as exc:
                    logger.exception("Image generation failed: %s", exc)
                    results[index] = {
                        "position": spec.get("position", index + 1),
                        "prompt": prompt,
                        "url": "",
                        "error": str(exc),
                    }

        await asyncio.gather(*(worker(index, spec) for index, spec in enumerate(specs)))
        return results
