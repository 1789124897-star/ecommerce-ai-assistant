from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.core.redis import cache_json, get_cached_json
from app.repositories.tasks import TaskRepository
from app.schemas.task import TaskResultResponse


class TaskQueryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repository = TaskRepository(db)

    async def get_task_result(self, task_id: str) -> dict:
        cache_key = f"task-result:{task_id}"
        cached = await get_cached_json(cache_key)
        if cached:
            return cached

        task = await self.repository.get_by_task_id(task_id)
        if not task:
            raise NotFoundError("Task not found")

        payload = TaskResultResponse(
            task_id=task.task_id,
            task_type=task.task_type,
            status=task.status.value,
            result=task.result_payload,
            error_message=task.error_message,
            retry_count=task.retry_count,
            duration_ms=task.duration_ms,
        ).model_dump()
        if task.status.value in {"SUCCESS", "FAILURE"}:
            await cache_json(cache_key, payload, settings.TASK_RESULT_CACHE_TTL)
        return payload

    async def list_tasks(
        self,
        *,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        tasks = await self.repository.list_tasks(
            status=status,
            task_type=task_type,
            limit=limit,
        )
        return [
            {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "status": task.status.value,
                "product_name": task.product_name,
                "submitted_by": task.submitted_by,
                "retry_count": task.retry_count,
                "duration_ms": task.duration_ms,
                "error_message": task.error_message,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "finished_at": task.finished_at.isoformat() if task.finished_at else None,
            }
            for task in tasks
        ]
