from typing import Any

from pydantic import BaseModel


class TaskSubmissionResponse(BaseModel):
    task_id: str
    task_type: str


class TaskResultResponse(BaseModel):
    task_id: str
    task_type: str
    status: str
    result: Any | None = None
    error_message: str | None = None
    retry_count: int = 0
    duration_ms: int | None = None
