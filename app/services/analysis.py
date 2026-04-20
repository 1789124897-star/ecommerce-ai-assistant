import json

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.image_utils import process_upload_image
from app.repositories.tasks import TaskRepository
from app.workers.tasks import (
    analyze_product_task,
    generate_detail_images_task,
    generate_main_images_task,
    generate_strategies_task,
)


class AnalysisSubmissionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.task_repository = TaskRepository(db)

    async def submit_analysis(
        self,
        *,
        product_name: str,
        function: str,
        price: str,
        extra: str,
        image: UploadFile,
        submitted_by: str,
    ) -> str:
        image_base64, mime = await process_upload_image(image)
        task = analyze_product_task.delay(
            name=product_name,
            function=function,
            price=price,
            extra=extra,
            image_base64=image_base64,
            image_mime=mime,
        )
        await self.task_repository.create_task(
            task_id=task.id,
            task_type="analysis",
            product_name=product_name,
            request_payload={
                "name": product_name,
                "function": function,
                "price": price,
                "extra": extra,
                "image_mime": mime,
            },
            submitted_by=submitted_by,
        )
        return task.id

    async def submit_strategy_generation(self, *, analysis: str, submitted_by: str) -> str:
        task = generate_strategies_task.delay(analysis=analysis)
        await self.task_repository.create_task(
            task_id=task.id,
            task_type="strategy",
            product_name=None,
            request_payload={"analysis": analysis},
            submitted_by=submitted_by,
        )
        return task.id

    async def submit_image_generation(
        self,
        *,
        image: UploadFile,
        specs_json: str,
        task_type: str,
        submitted_by: str,
    ) -> str:
        image_base64, mime = await process_upload_image(image)
        json.loads(specs_json)
        if task_type == "main_image":
            task = generate_main_images_task.delay(
                product_image_base64=image_base64,
                product_image_mime=mime,
                main_images_specs_json=specs_json,
            )
        else:
            task = generate_detail_images_task.delay(
                product_image_base64=image_base64,
                product_image_mime=mime,
                detail_pages_specs_json=specs_json,
            )
        await self.task_repository.create_task(
            task_id=task.id,
            task_type=task_type,
            product_name=image.filename,
            request_payload={"specs_json": specs_json, "image_mime": mime},
            submitted_by=submitted_by,
        )
        return task.id
