from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.core.redis import redis_client
from app.core.responses import success_response


router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(db_session)) -> dict:
    await db.execute(text("SELECT 1"))
    await redis_client.ping()
    return success_response(
        data={"database": "connected", "redis": "connected"},
        message="service healthy",
    )
