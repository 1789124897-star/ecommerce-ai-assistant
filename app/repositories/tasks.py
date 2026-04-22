from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func, select
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
            # Ensure task.started_at is timezone-aware
            if task.started_at.tzinfo is None:
                task.started_at = task.started_at.replace(tzinfo=timezone.utc)
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
            # Ensure task.started_at is timezone-aware
            if task.started_at.tzinfo is None:
                task.started_at = task.started_at.replace(tzinfo=timezone.utc)
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

    async def list_tasks(
        self,
        *,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 20,
    ) -> list[TaskRecord]:
        stmt = select(TaskRecord).order_by(TaskRecord.created_at.desc())
        if status:
            stmt = stmt.where(TaskRecord.status == status)
        if task_type:
            stmt = stmt.where(TaskRecord.task_type == task_type)
        stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_task_stats(self) -> dict:
        # 各状态任务数量
        status_stmt = select(TaskRecord.status, func.count(TaskRecord.id)).group_by(TaskRecord.status)
        status_result = await self.db.execute(status_stmt)
        status_counts = {row[0].value: row[1] for row in status_result.all()}

        # 各任务类型数量
        type_stmt = select(TaskRecord.task_type, func.count(TaskRecord.id)).group_by(TaskRecord.task_type)
        type_result = await self.db.execute(type_stmt)
        type_counts = {row[0]: row[1] for row in type_result.all()}

        # 总任务数
        total_result = await self.db.execute(select(func.count(TaskRecord.id)))
        total = total_result.scalar() or 0

        # 今日新增
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_result = await self.db.execute(
            select(func.count(TaskRecord.id)).where(TaskRecord.created_at >= today)
        )
        today_count = today_result.scalar() or 0

        # 平均耗时（仅统计已完成的）
        avg_result = await self.db.execute(
            select(func.avg(TaskRecord.duration_ms)).where(TaskRecord.duration_ms.isnot(None))
        )
        avg_duration = avg_result.scalar()

        return {
            "total": total,
            "today": today_count,
            "by_status": status_counts,
            "by_task_type": type_counts,
            "avg_duration_ms": int(avg_duration) if avg_duration else 0,
        }
