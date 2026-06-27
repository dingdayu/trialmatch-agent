from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, BigInteger, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("subjects.id", ondelete="SET NULL"), index=True
    )
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_type: Mapped[str] = mapped_column(String(32), nullable=False)
    file_scope: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(128))
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger)
    page_count: Mapped[Optional[int]] = mapped_column(Integer)
    parse_status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    description: Mapped[Optional[str]] = mapped_column(String(512))
    uploaded_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship("Project", back_populates="files", foreign_keys=[project_id])
    subject: Mapped["Subject"] = relationship("Subject", back_populates="files", foreign_keys=[subject_id])
    uploader: Mapped["User"] = relationship("User", back_populates="files_uploaded", foreign_keys=[uploaded_by])
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="file", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<UploadedFile {self.file_name}>"
