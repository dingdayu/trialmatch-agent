from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CriterionEvaluation(Base):
    __tablename__ = "criterion_evaluations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("screening_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    criterion_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("eligibility_criteria.id"), nullable=False, index=True
    )
    criterion_code: Mapped[str] = mapped_column(String(16), nullable=False)
    criterion_type: Mapped[str] = mapped_column(String(16), nullable=False)
    criterion_text: Mapped[str] = mapped_column(Text, nullable=False)
    ai_result: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence_score: Mapped[Optional[int]] = mapped_column(Integer)
    ai_rationale: Mapped[Optional[str]] = mapped_column(Text)
    manual_result: Mapped[Optional[str]] = mapped_column(String(32))
    manual_comment: Mapped[Optional[str]] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(16), nullable=False, default="unreviewed")
    reviewer_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    screening_run: Mapped["ScreeningRun"] = relationship("ScreeningRun", back_populates="evaluations")
    criterion: Mapped["EligibilityCriterion"] = relationship("EligibilityCriterion", back_populates="evaluations")
    reviewer: Mapped["User"] = relationship("User", back_populates="evaluations_reviewed", foreign_keys=[reviewer_id])
    citations: Mapped[list["EvaluationCitation"]] = relationship(
        "EvaluationCitation", back_populates="evaluation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CriterionEvaluation {self.criterion_code} ai={self.ai_result}>"
