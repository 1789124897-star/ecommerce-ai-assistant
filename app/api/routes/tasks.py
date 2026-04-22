from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.core.responses import success_response
from app.core.security import get_current_user
from app.services.tasks import TaskQueryService


router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/")
async def list_tasks(
    status: Optional[Literal["PENDING", "STARTED", "RETRY", "SUCCESS", "FAILURE"]] = Query(None, description="按任务状态筛选"),
    task_type: Optional[Literal["analysis", "strategy", "main_image", "detail_image"]] = Query(None, description="按任务类型筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回数量，默认20，最大100"),
    db: AsyncSession = Depends(db_session),
    user: dict = Depends(get_current_user),
) -> dict:
    result = await TaskQueryService(db).list_tasks(status=status, task_type=task_type, limit=limit)
    return success_response(data=result, message="tasks list fetched")


@router.get("/{task_id}")
async def get_task_result(
    task_id: str,
    db: AsyncSession = Depends(db_session),
    user: dict = Depends(get_current_user),
) -> dict:
    result = await TaskQueryService(db).get_task_result(task_id)
    return success_response(data=result, message="task result fetched")

@router.get("/stats")
async def get_task_stats(
    db: AsyncSession = Depends(db_session),
    user: dict = Depends(get_current_user),
) -> dict:
    result = await TaskQueryService(db).get_task_stats()
    return success_response(data=result, message="tasks list fetched")

