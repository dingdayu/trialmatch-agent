from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    study_name: Mapped[str] = mapped_column(String(512), nullable=False)
    study_short_name: Mapped[Optional[str]] = mapped_column(String(256))
    indication: Mapped[Optional[str]] = mapped_column(String(256), index=True)
    phase: Mapped[Optional[str]] = mapped_column(String(64))
    sponsor: Mapped[Optional[str]] = mapped_column(String(256))
    principal_investigator: Mapped[Optional[str]] = mapped_column(String(256))
    project_manager: Mapped[Optional[str]] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    ai_prompt: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    creator: Mapped["User"] = relationship("User", back_populates="projects", foreign_keys=[created_by])
    criteria: Mapped[list["EligibilityCriterion"]] = relationship(
        "EligibilityCriterion", back_populates="project", cascade="all, delete-orphan"
    )
    subjects: Mapped[list["Subject"]] = relationship(
        "Subject", back_populates="project", cascade="all, delete-orphan"
    )
    files: Mapped[list["UploadedFile"]] = relationship(
        "UploadedFile", back_populates="project", foreign_keys="UploadedFile.project_id"
    )

    def __repr__(self) -> str:
        return f"<Project {self.project_no}: {self.study_name}>"
