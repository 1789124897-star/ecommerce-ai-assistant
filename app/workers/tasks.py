import asyncio
import nest_asyncio
import json
from typing import Any

from celery import Task

from app.core.database import AsyncSessionLocal
from app.core.redis import redis_client
from app.core.logging import get_logger
from app.image_utils import decode_and_process_image, image_bytes_to_base64_url
from app.prompts import STRATEGY_TYPES, build_analysis_prompt, build_strategy_prompt
from app.repositories.tasks import TaskRepository
from app.services.ai_client import AIClient
from app.workers.celery_app import celery_app

nest_asyncio.apply()

logger = get_logger(__name__)


def run_async(coro):
    return asyncio.run(coro)


async def _mark_started(task_id: str) -> None:
    async with AsyncSessionLocal() as session:
        await TaskRepository(session).mark_started(task_id)


async def _mark_retry(task_id: str, error_message: str) -> None:
    async with AsyncSessionLocal() as session:
        await TaskRepository(session).mark_retry(task_id, error_message)


async def _mark_success(task_id: str, result_payload: dict[str, Any]) -> None:
    async with AsyncSessionLocal() as session:
        await TaskRepository(session).mark_success(task_id, result_payload)


async def _mark_failure(task_id: str, error_message: str) -> None:
    async with AsyncSessionLocal() as session:
        await TaskRepository(session).mark_failure(task_id, error_message)


async def _save_assets(task_id: str, assets: list[dict[str, Any]], image_type: str) -> None:
    async with AsyncSessionLocal() as session:
        await TaskRepository(session).save_generated_assets(task_id, assets, image_type)


def _build_image_payload(image_base64: str, image_mime: str, compress: bool) -> str:
    image_bytes, final_mime = decode_and_process_image(
        image_base64=image_base64,
        original_mime=image_mime,
        compress=compress,
    )
    return image_bytes_to_base64_url(image_bytes, final_mime)


def _load_specs(specs_json: str) -> list[dict[str, Any]]:
    specs = json.loads(specs_json)
    if not isinstance(specs, list) or len(specs) != 5:
        raise ValueError("Specs must be a list containing exactly 5 items")
    return specs


@celery_app.task(name="app.workers.tasks.system_heartbeat_task")
def system_heartbeat_task():
    logger.info("Running periodic system heartbeat task.")
    run_async(redis_client.ping())
    return {"status": "ok", "message": "heartbeat executed"}


@celery_app.task(bind=True, name="app.workers.tasks.analyze_product_task", max_retries=3)
def analyze_product_task(
    self: Task,
    *,
    name: str,
    function: str,
    price: str,
    extra: str,
    image_base64: str,
    image_mime: str,
):
    run_async(_mark_started(self.request.id))
    client = AIClient()
    try:
        image_data_url = _build_image_payload(image_base64, image_mime, compress=True)
        prompt = build_analysis_prompt(
            name=name,
            function=function,
            price=price,
            extra=extra,
        )
        analysis_text = run_async(
            client.analyze_product(prompt=prompt, image_data_url=image_data_url)
        )
        result = {
            "analysis": analysis_text,
            "product_name": name,
            "used_multimodal": True,
        }
        run_async(_mark_success(self.request.id, result))
        return result
    except Exception as exc:
        logger.exception("Analysis task failed: %s", exc)
        run_async(_mark_retry(self.request.id, str(exc)))
        try:
            raise self.retry(exc=exc, countdown=60, max_retries=3)
        except Exception:
            run_async(_mark_failure(self.request.id, str(exc)))
            raise


@celery_app.task(bind=True, name="app.workers.tasks.generate_strategies_task", max_retries=2)
def generate_strategies_task(self: Task, *, analysis: str):
    run_async(_mark_started(self.request.id))
    client = AIClient()

    async def generate_all() -> dict[str, Any]:
        coroutines = [
            client.generate_strategy(
                prompt=build_strategy_prompt(
                    analysis=analysis,
                    strategy_code=code,
                    strategy_name=name,
                )
            )
            for code, name in STRATEGY_TYPES.items()
        ]
        results = await asyncio.gather(*coroutines)
        return {"strategies": dict(zip(STRATEGY_TYPES.keys(), results))}

    try:
        result = run_async(generate_all())
        run_async(_mark_success(self.request.id, result))
        return result
    except Exception as exc:
        logger.exception("Strategy task failed: %s", exc)
        run_async(_mark_retry(self.request.id, str(exc)))
        try:
            raise self.retry(exc=exc, countdown=30, max_retries=2)
        except Exception:
            run_async(_mark_failure(self.request.id, str(exc)))
            raise


def _generate_images_common(
    *,
    task_id: str,
    product_image_base64: str,
    product_image_mime: str,
    specs_json: str,
    image_type: str,
    default_size: str,
) -> dict[str, Any]:
    specs = _load_specs(specs_json)
    image_data_url = _build_image_payload(
        product_image_base64,
        product_image_mime,
        compress=False,
    )
    client = AIClient()
    result = {
        "images": run_async(
            client.generate_images(
                specs=specs,
                image_data_url=image_data_url,
                size=default_size,
            )
        )
    }
    run_async(_save_assets(task_id, result["images"], image_type))
    return result


@celery_app.task(bind=True, name="app.workers.tasks.generate_main_images_task", max_retries=2)
def generate_main_images_task(
    self: Task,
    *,
    product_image_base64: str,
    product_image_mime: str,
    main_images_specs_json: str,
):
    run_async(_mark_started(self.request.id))
    try:
        result = _generate_images_common(
            task_id=self.request.id,
            product_image_base64=product_image_base64,
            product_image_mime=product_image_mime,
            specs_json=main_images_specs_json,
            image_type="main",
            default_size="2048x2048",
        )
        run_async(_mark_success(self.request.id, result))
        return result
    except Exception as exc:
        logger.exception("Main image task failed: %s", exc)
        run_async(_mark_retry(self.request.id, str(exc)))
        try:
            raise self.retry(exc=exc, countdown=30, max_retries=2)
        except Exception:
            run_async(_mark_failure(self.request.id, str(exc)))
            raise


@celery_app.task(bind=True, name="app.workers.tasks.generate_detail_images_task", max_retries=2)
def generate_detail_images_task(
    self: Task,
    *,
    product_image_base64: str,
    product_image_mime: str,
    detail_pages_specs_json: str,
):
    run_async(_mark_started(self.request.id))
    try:
        result = _generate_images_common(
            task_id=self.request.id,
            product_image_base64=product_image_base64,
            product_image_mime=product_image_mime,
            specs_json=detail_pages_specs_json,
            image_type="detail",
            default_size="2048x2048",
        )
        run_async(_mark_success(self.request.id, result))
        return result
    except Exception as exc:
        logger.exception("Detail image task failed: %s", exc)
        run_async(_mark_retry(self.request.id, str(exc)))
        try:
            raise self.retry(exc=exc, countdown=30, max_retries=2)
        except Exception:
            run_async(_mark_failure(self.request.id, str(exc)))
            raise
