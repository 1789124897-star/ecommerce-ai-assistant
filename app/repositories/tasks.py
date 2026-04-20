from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GeneratedAsset, TaskRecord, TaskStatus


class TaskRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_task(
        self,
        *,
        task_id: str,
        task_type: str,
        product_name: Optional[str],
        request_payload: dict[str, Any],
        submitted_by: str,
    ) -> TaskRecord:
        task = TaskRecord(
            task_id=task_id,
            task_type=task_type,
            product_name=product_name,
            status=TaskStatus.PENDING,
            request_payload=request_payload,
            submitted_by=submitted_by,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_by_task_id(self, task_id: str) -> Optional[TaskRecord]:
        result = await self.db.execute(
            select(TaskRecord).where(TaskRecord.task_id == task_id)
        )
        return result.scalar_one_or_none()

    async def mark_started(self, task_id: str) -> None:
        task = await self.get_by_task_id(task_id)
        if not task:
            return
        task.status = TaskStatus.STARTED
        task.started_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def mark_retry(self, task_id: str, error_message: str) -> None:
        task = await self.get_by_task_id(task_id)
        if not task:
            return
        task.status = TaskStatus.RETRY
        task.error_message = error_message
        task.retry_count += 1
        await self.db.commit()

    async def mark_success(self, task_id: str, result_payload: dict[str, Any]) -> None:
        task = await self.get_by_task_id(task_id)
        if not task:
            return
        finished_at = datetime.now(timezone.utc)
        task.status = TaskStatus.SUCCESS
        task.result_payload = result_payload
        task.error_message = None
        task.finished_at = finished_at
        if task.started_at:
            task.duration_ms = int((finished_at - task.started_at).total_seconds() * 1000)
        await self.db.commit()

    async def mark_failure(self, task_id: str, error_message: str) -> None:
        task = await self.get_by_task_id(task_id)
        if not task:
            return
        finished_at = datetime.now(timezone.utc)
        task.status = TaskStatus.FAILURE
        task.error_message = error_message
        task.finished_at = finished_at
        if task.started_at:
            task.duration_ms = int((finished_at - task.started_at).total_seconds() * 1000)
        await self.db.commit()

    async def save_generated_assets(
        self,
        task_id: str,
        assets: list[dict[str, Any]],
        image_type: str,
    ) -> None:
        for asset in assets:
            self.db.add(
                GeneratedAsset(
                    task_id=task_id,
                    image_type=image_type,
                    position=asset.get("position", 0),
                    prompt=asset.get("prompt", ""),
                    image_url=asset.get("url", ""),
                )
            )
        await self.db.commit()
