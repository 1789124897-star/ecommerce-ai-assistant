import enum
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Enum, Integer, JSON, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    RETRY = "RETRY"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class TaskRecord(Base):
    __tablename__ = "task_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    task_type: Mapped[str] = mapped_column(String(32), index=True)
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
    )
    submitted_by: Mapped[str] = mapped_column(String(64), default="system")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    request_payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    result_payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class GeneratedAsset(Base):
    __tablename__ = "generated_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[str] = mapped_column(String(64), index=True)
    image_type: Mapped[str] = mapped_column(String(16))
    position: Mapped[int] = mapped_column(Integer)
    prompt: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
