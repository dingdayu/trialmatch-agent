from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EvaluationCitation(Base):
    __tablename__ = "evaluation_citations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    evaluation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("criterion_evaluations.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    file_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("uploaded_files.id", ondelete="SET NULL"), index=True
    )
    file_name: Mapped[Optional[str]] = mapped_column(String(512))
    file_type: Mapped[Optional[str]] = mapped_column(String(32))
    page_no: Mapped[Optional[int]] = mapped_column(Integer)
    chunk_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("document_chunks.id", ondelete="SET NULL")
    )
    quoted_text: Mapped[Optional[str]] = mapped_column(Text)
    extracted_fact: Mapped[Optional[str]] = mapped_column(Text)
    relevance_explanation: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    evaluation: Mapped["CriterionEvaluation"] = relationship(
        "CriterionEvaluation", back_populates="citations"
    )

    def __repr__(self) -> str:
        return f"<EvaluationCitation eval={self.evaluation_id} file={self.file_name}>"
