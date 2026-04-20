from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.core.responses import success_response
from app.core.security import get_current_user
from app.services.tasks import TaskQueryService


router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/{task_id}")
async def get_task_result(
    task_id: str,
    db: AsyncSession = Depends(db_session),
    user: dict = Depends(get_current_user),
) -> dict:
    result = await TaskQueryService(db).get_task_result(task_id)
    return success_response(data=result, message="task result fetched")
