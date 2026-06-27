from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_no: Mapped[str] = mapped_column(String(64), nullable=False)
    site_name: Mapped[Optional[str]] = mapped_column(String(256))
    gender: Mapped[Optional[str]] = mapped_column(String(8))
    age: Mapped[Optional[int]] = mapped_column(Integer)
    birth_year: Mapped[Optional[int]] = mapped_column(Integer)
    diagnosis: Mapped[Optional[str]] = mapped_column(String(512))
    remark: Mapped[Optional[str]] = mapped_column(String(1024))
    material_count: Mapped[int] = mapped_column(Integer, default=0)
    screening_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="not_started", index=True
    )
    overall_result: Mapped[Optional[str]] = mapped_column(String(32))
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped["Project"] = relationship("Project", back_populates="subjects")
    files: Mapped[list["UploadedFile"]] = relationship(
        "UploadedFile", back_populates="subject", foreign_keys="UploadedFile.subject_id"
    )
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="subject", foreign_keys="DocumentChunk.subject_id"
    )
    screening_runs: Mapped[list["ScreeningRun"]] = relationship(
        "ScreeningRun", back_populates="subject", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Subject {self.subject_no}>"
