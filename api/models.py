from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum as PyEnum
from api import Base

class TaskStatus(PyEnum):
    pending = "pending"
    processing = "processing"
    done = "done"

class ImageTask(Base):
    __tablename__ = "image_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(Enum(TaskStatus), default=TaskStatus.pending)
    upload_time: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
