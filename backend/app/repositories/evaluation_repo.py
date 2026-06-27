"""匹配结果数据访问层 — 对应 Task 13.2, 14.1"""

from __future__ import annotations

from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.evaluation import CriterionEvaluation
from app.models.citation import EvaluationCitation


class EvaluationRepository:
    """匹配结果数据访问层"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, evaluation_id: str) -> Optional[CriterionEvaluation]:
        result = await self.db.execute(
            select(CriterionEvaluation).where(CriterionEvaluation.id == evaluation_id)
        )
        return result.scalar_one_or_none()

    async def list_by_run(
        self,
        run_id: str,
        criterion_type: Optional[str] = None,
        ai_result: Optional[str] = None,
        review_status: Optional[str] = None,
    ) -> List[CriterionEvaluation]:
        query = select(CriterionEvaluation).where(CriterionEvaluation.run_id == run_id)
        if criterion_type:
            query = query.where(CriterionEvaluation.criterion_type == criterion_type)
        if ai_result:
            query = query.where(CriterionEvaluation.ai_result == ai_result)
        if review_status:
            query = query.where(CriterionEvaluation.review_status == review_status)

        query = query.order_by(CriterionEvaluation.criterion_type, CriterionEvaluation.criterion_code)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_subject_latest(
        self,
        subject_id: str,
        criterion_type: Optional[str] = None,
        ai_result: Optional[str] = None,
        review_status: Optional[str] = None,
    ) -> Optional[tuple]:
        """获取受试者最新匹配结果（含 run）"""
        from app.models.screening_run import ScreeningRun

        # 找到最新完成的 run
        run_result = await self.db.execute(
            select(ScreeningRun)
            .where(ScreeningRun.subject_id == subject_id, ScreeningRun.status == "completed")
            .order_by(ScreeningRun.completed_at.desc())
            .limit(1)
        )
        latest_run = run_result.scalar_one_or_none()
        if not latest_run:
            return None

        evaluations = await self.list_by_run(
            run_id=latest_run.id,
            criterion_type=criterion_type,
            ai_result=ai_result,
            review_status=review_status,
        )

        return latest_run, evaluations

    async def get_citations(self, evaluation_id: str) -> List[EvaluationCitation]:
        result = await self.db.execute(
            select(EvaluationCitation).where(
                EvaluationCitation.evaluation_id == evaluation_id
            )
        )
        return list(result.scalars().all())

    async def get_citation_context(
        self, citation_id: str, before: int = 1, after: int = 1
    ) -> Optional[dict]:
        """获取引用原文上下文 — 接口 #44"""
        cit_result = await self.db.execute(
            select(EvaluationCitation).where(EvaluationCitation.id == citation_id)
        )
        citation = cit_result.scalar_one_or_none()
        if not citation:
            return None

        context = {
            "citation": citation,
            "surrounding_chunks": [],
        }

        if citation.chunk_id:
            from app.models.document_chunk import DocumentChunk
            chunk_result = await self.db.execute(
                select(DocumentChunk).where(DocumentChunk.id == citation.chunk_id)
            )
            target_chunk = chunk_result.scalar_one_or_none()
            if target_chunk:
                # 查询相邻 chunks
                chunk_range = await self.db.execute(
                    select(DocumentChunk)
                    .where(
                        DocumentChunk.file_id == target_chunk.file_id,
                        DocumentChunk.page_no == target_chunk.page_no,
                        DocumentChunk.chunk_index >= target_chunk.chunk_index - before,
                        DocumentChunk.chunk_index <= target_chunk.chunk_index + after,
                    )
                    .order_by(DocumentChunk.chunk_index)
                )
                context["surrounding_chunks"] = list(chunk_range.scalars().all())

        return context

    async def batch_update_review_status(
        self, evaluation_ids: List[str], review_status: str, reviewer_id: str
    ) -> int:
        """批量更新复核状态"""
        from datetime import datetime, timezone

        count = 0
        for eid in evaluation_ids:
            ev = await self.get_by_id(eid)
            if ev:
                ev.review_status = review_status
                ev.reviewer_id = reviewer_id
                ev.reviewed_at = datetime.now(timezone.utc)
                count += 1
        await self.db.commit()
        return count
