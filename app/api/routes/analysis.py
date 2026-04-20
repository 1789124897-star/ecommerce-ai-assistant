from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.core.config import settings
from app.core.responses import success_response
from app.core.security import get_current_user
from app.schemas.task import TaskSubmissionResponse
from app.services.analysis import AnalysisSubmissionService


router = APIRouter(prefix="/analysis", tags=["Analysis"])
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)


@router.post("/submit")
@limiter.limit("10/minute")
async def submit_analysis(
    request: Request,
    name: str = Form(...),
    function: str = Form(...),
    price: str = Form(...),
    extra: str = Form(""),
    image: UploadFile = File(...),
    db: AsyncSession = Depends(db_session),
    user: dict = Depends(get_current_user),
) -> dict:
    task_id = await AnalysisSubmissionService(db).submit_analysis(
        product_name=name,
        function=function,
        price=price,
        extra=extra,
        image=image,
        submitted_by=user["sub"],
    )
    data = TaskSubmissionResponse(task_id=task_id, task_type="analysis").model_dump()
    return success_response(data=data, message="analysis task submitted")


@router.post("/strategies")
@limiter.limit("10/minute")
async def submit_strategy_generation(
    request: Request,
    analysis: str = Form(...),
    db: AsyncSession = Depends(db_session),
    user: dict = Depends(get_current_user),
) -> dict:
    task_id = await AnalysisSubmissionService(db).submit_strategy_generation(
        analysis=analysis,
        submitted_by=user["sub"],
    )
    data = TaskSubmissionResponse(task_id=task_id, task_type="strategy").model_dump()
    return success_response(data=data, message="strategy task submitted")


@router.post("/images/main")
@limiter.limit("5/minute")
async def submit_main_image_generation(
    request: Request,
    product_image: UploadFile = File(...),
    main_images_data: str = Form(...),
    db: AsyncSession = Depends(db_session),
    user: dict = Depends(get_current_user),
) -> dict:
    task_id = await AnalysisSubmissionService(db).submit_image_generation(
        image=product_image,
        specs_json=main_images_data,
        task_type="main_image",
        submitted_by=user["sub"],
    )
    data = TaskSubmissionResponse(task_id=task_id, task_type="main_image").model_dump()
    return success_response(data=data, message="main image task submitted")


@router.post("/images/detail")
@limiter.limit("5/minute")
async def submit_detail_image_generation(
    request: Request,
    product_image: UploadFile = File(...),
    detail_pages_data: str = Form(...),
    db: AsyncSession = Depends(db_session),
    user: dict = Depends(get_current_user),
) -> dict:
    task_id = await AnalysisSubmissionService(db).submit_image_generation(
        image=product_image,
        specs_json=detail_pages_data,
        task_type="detail_image",
        submitted_by=user["sub"],
    )
    data = TaskSubmissionResponse(task_id=task_id, task_type="detail_image").model_dump()
    return success_response(data=data, message="detail image task submitted")
