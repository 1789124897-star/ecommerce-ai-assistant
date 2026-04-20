from typing import Any, Optional

from pydantic import BaseModel


class TaskSubmissionResponse(BaseModel):
    task_id: str
    task_type: str


class TaskResultResponse(BaseModel):
    task_id: str
    task_type: str
    status: str
    result: Optional[Any] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    duration_ms: Optional[int] = None
