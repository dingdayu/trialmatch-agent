from __future__ import annotations

from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone

from app.models.evaluation import CriterionEvaluation
from app.models.citation import EvaluationCitation
from app.models.screening_run import ScreeningRun
from app.models.subject import Subject
from app.models.project import Project


class EvaluationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_latest_evaluations(
        self,
        subject_id: str,
        criterion_type: Optional[str] = None,
        ai_result: Optional[str] = None,
        review_status: Optional[str] = None,
    ) -> Optional[dict]:
        """获取受试者最新一次分析的匹配结果"""
        # 找到最新的 screening_run
        run_result = await self.db.execute(
            select(ScreeningRun)
            .where(
                ScreeningRun.subject_id == subject_id,
                ScreeningRun.status == "completed",
            )
            .order_by(ScreeningRun.completed_at.desc())
            .limit(1)
        )
        latest_run = run_result.scalar_one_or_none()
        if not latest_run:
            return None

        # 查询受试者和项目
        subject_result = await self.db.execute(
            select(Subject).where(Subject.id == subject_id)
        )
        subject = subject_result.scalar_one_or_none()
        if not subject:
            return None

        project_result = await self.db.execute(
            select(Project).where(Project.id == subject.project_id)
        )
        project = project_result.scalar_one_or_none()

        # 查询 evaluations
        query = select(CriterionEvaluation).where(
            CriterionEvaluation.run_id == latest_run.id
        )
        if criterion_type:
            query = query.where(CriterionEvaluation.criterion_type == criterion_type)
        if ai_result:
            query = query.where(CriterionEvaluation.ai_result == ai_result)
        if review_status:
            query = query.where(CriterionEvaluation.review_status == review_status)

        query = query.order_by(CriterionEvaluation.criterion_type, CriterionEvaluation.criterion_code)
        result = await self.db.execute(query)
        evaluations = list(result.scalars().all())

        # 计算 citation_count
        for ev in evaluations:
            count_result = await self.db.execute(
                select(func.count()).select_from(EvaluationCitation).where(
                    EvaluationCitation.evaluation_id == ev.id
                )
            )
            ev._citation_count = count_result.scalar() or 0

        # 汇总统计
        summary = self._build_summary(evaluations)

        return {
            "run_id": latest_run.id,
            "subject": {
                "id": subject.id,
                "subject_no": subject.subject_no,
                "site_name": subject.site_name,
                "gender": subject.gender,
                "age": subject.age,
                "diagnosis": subject.diagnosis,
            },
            "project": {
                "id": project.id if project else None,
                "project_no": project.project_no if project else None,
                "study_name": project.study_name if project else None,
            },
            "summary": summary,
            "evaluations": evaluations,
        }

    async def get_evaluation_detail(self, evaluation_id: str) -> Optional[CriterionEvaluation]:
        """获取单条匹配结果详情（含证据引用）"""
        result = await self.db.execute(
            select(CriterionEvaluation).where(CriterionEvaluation.id == evaluation_id)
        )
        evaluation = result.scalar_one_or_none()
        if evaluation:
            citations_result = await self.db.execute(
                select(EvaluationCitation).where(
                    EvaluationCitation.evaluation_id == evaluation_id
                )
            )
            evaluation._citations = list(citations_result.scalars().all())
        return evaluation

    async def manual_review(
        self,
        evaluation_id: str,
        manual_result: str,
        manual_comment: Optional[str],
        review_status: str,
        reviewer_id: str,
    ) -> CriterionEvaluation:
        """人工复核单条标准"""
        result = await self.db.execute(
            select(CriterionEvaluation).where(CriterionEvaluation.id == evaluation_id)
        )
        evaluation = result.scalar_one_or_none()
        if not evaluation:
            raise ValueError(f"匹配结果 {evaluation_id} 不存在")

        evaluation.manual_result = manual_result
        evaluation.manual_comment = manual_comment
        evaluation.review_status = review_status
        evaluation.reviewer_id = reviewer_id
        evaluation.reviewed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(evaluation)
        return evaluation

    async def batch_review(
        self,
        evaluation_ids: List[str],
        manual_comment: Optional[str],
        reviewer_id: str,
    ) -> int:
        """批量人工确认"""
        count = 0
        for eid in evaluation_ids:
            await self.manual_review(eid, "pass", manual_comment, "reviewed", reviewer_id)
            count += 1
        return count

    def _build_summary(self, evaluations: List[CriterionEvaluation]) -> dict:
        """构建初筛汇总统计"""
        inclusion_pass = 0
        inclusion_fail = 0
        inclusion_insufficient = 0
        exclusion_hit = 0
        exclusion_not_hit = 0
        exclusion_insufficient = 0
        manual_review = 0

        for e in evaluations:
            if e.ai_result == "manual_review":
                manual_review += 1
            if e.criterion_type == "inclusion":
                if e.ai_result == "pass":
                    inclusion_pass += 1
                elif e.ai_result == "fail":
                    inclusion_fail += 1
                elif e.ai_result in ("insufficient_data", "manual_review"):
                    inclusion_insufficient += 1
            elif e.criterion_type == "exclusion":
                if e.ai_result == "exclusion_hit":
                    exclusion_hit += 1
                elif e.ai_result == "exclusion_not_hit":
                    exclusion_not_hit += 1
                elif e.ai_result in ("insufficient_data", "manual_review"):
                    exclusion_insufficient += 1

        return {
            "overall_result": _compute_overall_result(evaluations),
            "score": _compute_overall_score(evaluations),
            "ai_advice": None,  # 后续 AI 引擎会生成
            "inclusion_pass_count": inclusion_pass,
            "inclusion_fail_count": inclusion_fail,
            "inclusion_insufficient_count": inclusion_insufficient,
            "exclusion_hit_count": exclusion_hit,
            "exclusion_not_hit_count": exclusion_not_hit,
            "exclusion_insufficient_count": exclusion_insufficient,
            "manual_review_count": manual_review,
        }


def _compute_overall_result(evaluations: List[CriterionEvaluation]) -> str:
    """按技术文档 5.4 节的规则计算总体结论"""
    if not evaluations:
        return "insufficient_data"

    inclusion_fail = sum(1 for e in evaluations if e.criterion_type == "inclusion" and e.ai_result == "fail")
    inclusion_insufficient = sum(
        1 for e in evaluations
        if e.criterion_type == "inclusion"
        and e.ai_result in ("insufficient_data", "manual_review")
    )
    exclusion_hit = sum(1 for e in evaluations if e.criterion_type == "exclusion" and e.ai_result == "exclusion_hit")
    exclusion_insufficient = sum(
        1 for e in evaluations
        if e.criterion_type == "exclusion"
        and e.ai_result in ("insufficient_data", "manual_review")
    )
    has_pending = any(e.ai_result == "manual_review" for e in evaluations)

    if exclusion_hit > 0:
        return "excluded"
    if inclusion_fail > 0 or inclusion_insufficient > 0 or exclusion_insufficient > 0:
        return "manual_review" if has_pending else "insufficient_data"
    if has_pending:
        return "manual_review"
    return "recommended"


def _compute_overall_score(evaluations: List[CriterionEvaluation]) -> int:
    """按技术文档 5.4 节规则计算综合评分"""
    if not evaluations:
        return 0
    total_weight = 0
    weighted_sum = 0
    for e in evaluations:
        weight = 1.0
        if e.criterion_type == "exclusion" and e.ai_result == "exclusion_hit":
            weighted_sum += 0
            total_weight += weight * 2
            continue
        if e.criterion_type == "inclusion" and e.ai_result == "fail":
            weighted_sum += 0
            total_weight += weight
            continue
        score = e.confidence_score or 50
        if e.ai_result in ("insufficient_data", "manual_review"):
            weighted_sum += score * 0.5
        else:
            weighted_sum += score
        total_weight += weight

    return round(weighted_sum / total_weight) if total_weight > 0 else 0
