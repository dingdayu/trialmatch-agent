from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EligibilityCriterion(Base):
    __tablename__ = "eligibility_criteria"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    criterion_code: Mapped[str] = mapped_column(String(16), nullable=False)
    criterion_type: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    criterion_text: Mapped[str] = mapped_column(Text, nullable=False)
    criterion_explanation: Mapped[Optional[str]] = mapped_column(Text)
    ai_instruction: Mapped[Optional[str]] = mapped_column(Text)
    required_fields: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped["Project"] = relationship("Project", back_populates="criteria")
    evaluations: Mapped[list["CriterionEvaluation"]] = relationship(
        "CriterionEvaluation", back_populates="criterion", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Criterion {self.criterion_code} [{self.criterion_type}]>"
