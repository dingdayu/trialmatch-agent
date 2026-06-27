from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("uploaded_files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("subjects.id", ondelete="SET NULL"), index=True
    )
    page_no: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    bbox: Mapped[Optional[dict]] = mapped_column(JSON)
    extracted_entities: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    file: Mapped["UploadedFile"] = relationship("UploadedFile", back_populates="chunks")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="chunks", foreign_keys=[subject_id])

    def __repr__(self) -> str:
        return f"<DocumentChunk file={self.file_id} page={self.page_no} idx={self.chunk_index}>"
