"""AI 初筛服务 — 对应 Task 12.3"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.screening_run import ScreeningRun
from app.models.subject import Subject
from app.models.project import Project
from app.models.evaluation import CriterionEvaluation
from app.models.citation import EvaluationCitation
from app.models.criteria import EligibilityCriterion
from app.models.document_chunk import DocumentChunk
from app.utils.logger import logger


class ScreeningService:
    """AI 初筛服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_screening(
        self,
        subject_id: str,
        user_id: str,
        model_name: Optional[str] = None,
        prompt_version: Optional[str] = None,
        criteria_ids: Optional[List[str]] = None,
        force_reparse: bool = False,
    ) -> ScreeningRun:
        """启动单个 AI 初筛任务"""
        # 获取受试者
        subject = await self._get_subject(subject_id)

        # 校验：无运行中任务
        existing = await self.db.execute(
            select(ScreeningRun).where(
                ScreeningRun.subject_id == subject_id,
                ScreeningRun.status.in_(["queued", "running"]),
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("该受试者已有运行中的初筛任务")

        # 校验：文件已解析
        files_ready = await self._check_files_parsed(subject_id)
        if not files_ready and not force_reparse:
            raise ValueError("受试者文件尚未全部解析完成")

        # 创建 run 记录
        run_no = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        run = ScreeningRun(
            id=str(uuid.uuid4()),
            project_id=subject.project_id,
            subject_id=subject_id,
            run_no=run_no,
            status="queued",
            model_name=model_name,
            prompt_version=prompt_version,
            created_by=user_id,
        )
        self.db.add(run)

        # 更新受试者状态
        subject.screening_status = "screening"
        await self.db.commit()
        await self.db.refresh(run)

        logger.info(f"初筛任务已创建: {run_no} for subject {subject_id}")
        return run

    async def execute_screening(self, run_id: str) -> dict:
        """执行 AI 初筛（同步版本，供 API 直接调用）"""
        run = await self._get_run(run_id)
        if run.status not in ("queued", "running"):
            raise ValueError(f"任务状态为 {run.status}，无法执行")

        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        await self.db.commit()

        try:
            result = await self._run_screening_pipeline(run)
            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc)

            # 更新受试者总体结论
            subject = await self._get_subject(run.subject_id)
            subject.overall_result = result.get("overall_result")
            subject.screening_status = "screened"

            await self.db.commit()
            logger.info(f"初筛任务完成: {run.run_no}")
            return result
        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            await self.db.commit()
            logger.error(f"初筛任务失败: {run.run_no}, error={str(e)}")
            raise

    async def _run_screening_pipeline(self, run: ScreeningRun) -> dict:
        """执行初筛流水线：加载条件 → 调用 LLM → 写入结果"""
        from app.services.ai_engine import AIEngine

        # 加载标准和分片
        criteria_list = await self._load_criteria(run.project_id)
        chunks = await self._load_chunks(run.subject_id)
        subject = await self._get_subject(run.subject_id)
        project = await self._get_project(run.project_id)

        chunks_text = "\n\n".join([c.content for c in chunks])

        engine = AIEngine()
        evaluations = []

        for criterion in criteria_list:
            criterion_dict = {
                "id": criterion.id,
                "criterion_code": criterion.criterion_code,
                "criterion_type": criterion.criterion_type,
                "criterion_text": criterion.criterion_text,
                "criterion_explanation": criterion.criterion_explanation,
                "ai_instruction": criterion.ai_instruction,
            }

            subject_dict = {
                "subject_no": subject.subject_no,
                "gender": subject.gender,
                "age": subject.age,
                "diagnosis": subject.diagnosis,
                "site_name": subject.site_name,
            }

            ai_prompt = project.ai_prompt if project else None

            try:
                result = await engine.evaluate_criterion(
                    criterion=criterion_dict,
                    subject_info=subject_dict,
                    chunks_text=chunks_text,
                    ai_prompt=ai_prompt,
                )
            except Exception as e:
                logger.warning(f"标准 {criterion.criterion_code} 评估失败: {str(e)}")
                result = {
                    "criterion_id": criterion.id,
                    "criterion_code": criterion.criterion_code,
                    "criterion_type": criterion.criterion_type,
                    "criterion_text": criterion.criterion_text,
                    "ai_result": "insufficient_data",
                    "confidence_score": 0,
                    "ai_rationale": f"评估异常: {str(e)}",
                    "citations": [],
                }

            # 写入 evaluation 记录
            evaluation = CriterionEvaluation(
                id=str(uuid.uuid4()),
                run_id=run.id,
                project_id=run.project_id,
                subject_id=run.subject_id,
                criterion_id=criterion.id,
                criterion_code=criterion.criterion_code,
                criterion_type=criterion.criterion_type,
                criterion_text=criterion.criterion_text,
                ai_result=result["ai_result"],
                confidence_score=result.get("confidence_score", 50),
                ai_rationale=result.get("ai_rationale", ""),
                review_status="unreviewed",
            )
            self.db.add(evaluation)
            await self.db.flush()

            # 写入 citations
            for cit in result.get("citations", []):
                citation = EvaluationCitation(
                    id=str(uuid.uuid4()),
                    evaluation_id=evaluation.id,
                    quoted_text=cit.get("quoted_text", ""),
                    extracted_fact=cit.get("extracted_fact", ""),
                    relevance_explanation=cit.get("relevance_explanation", ""),
                )
                self.db.add(citation)

            evaluations.append(evaluation)

        # 计算总体结论
        overall_result = AIEngine.compute_overall_result(evaluations)
        overall_score = AIEngine.compute_overall_score(evaluations)

        return {
            "run_id": run.id,
            "overall_result": overall_result,
            "overall_score": overall_score,
            "evaluation_count": len(evaluations),
        }

    async def list_runs(
        self,
        subject_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ScreeningRun], int]:
        """获取初筛任务列表"""
        query = select(ScreeningRun).where(ScreeningRun.subject_id == subject_id)
        count_query = select(func.count()).select_from(ScreeningRun).where(
            ScreeningRun.subject_id == subject_id
        )

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(ScreeningRun.created_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_run_detail(self, run_id: str) -> ScreeningRun:
        """获取初筛任务详情"""
        run = await self._get_run(run_id)

        # 附加 summary
        ev_result = await self.db.execute(
            select(CriterionEvaluation).where(CriterionEvaluation.run_id == run_id)
        )
        evaluations = list(ev_result.scalars().all())

        run._summary = {  # type: ignore
            "overall_result": run.subject.overall_result if run.subject else None,
            "evaluation_count": len(evaluations),
        }
        return run

    async def rerun_screening(
        self,
        run_id: str,
        user_id: str,
        model_name: Optional[str] = None,
        prompt_version: Optional[str] = None,
        criteria_ids: Optional[List[str]] = None,
    ) -> ScreeningRun:
        """重新运行初筛"""
        old_run = await self._get_run(run_id)
        return await self.start_screening(
            subject_id=old_run.subject_id,
            user_id=user_id,
            model_name=model_name,
            prompt_version=prompt_version,
            criteria_ids=criteria_ids,
        )

    async def confirm_all(self, subject_id: str) -> int:
        """确认全部待复核结果"""
        # 找到最新 run
        run_result = await self.db.execute(
            select(ScreeningRun)
            .where(ScreeningRun.subject_id == subject_id, ScreeningRun.status == "completed")
            .order_by(ScreeningRun.completed_at.desc())
            .limit(1)
        )
        latest_run = run_result.scalar_one_or_none()
        if not latest_run:
            return 0

        # 批量确认
        ev_result = await self.db.execute(
            select(CriterionEvaluation).where(
                CriterionEvaluation.run_id == latest_run.id,
                CriterionEvaluation.review_status == "unreviewed",
            )
        )
        evaluations = list(ev_result.scalars().all())

        now = datetime.now(timezone.utc)
        for ev in evaluations:
            ev.review_status = "reviewed"
            ev.reviewed_at = now

        # 更新受试者状态
        subject = await self._get_subject(subject_id)
        subject.screening_status = "completed"

        await self.db.commit()
        return len(evaluations)

    async def batch_start_screening(
        self,
        subject_ids: List[str],
        user_id: str,
        model_name: Optional[str] = None,
        prompt_version: Optional[str] = None,
        criteria_ids: Optional[List[str]] = None,
        force_reparse: bool = False,
    ) -> dict:
        """批量启动初筛"""
        import uuid as uuid_mod
        batch_id = f"BATCH-{uuid_mod.uuid4().hex[:8]}"
        runs = []
        skipped = []
        skipped_reasons = []

        for sid in subject_ids:
            try:
                run = await self.start_screening(
                    subject_id=sid,
                    user_id=user_id,
                    model_name=model_name,
                    prompt_version=prompt_version,
                    criteria_ids=criteria_ids,
                    force_reparse=force_reparse,
                )
                runs.append(run)
            except ValueError as e:
                skipped.append(sid)
                skipped_reasons.append(str(e))

        return {
            "batch_id": batch_id,
            "runs": runs,
            "skipped_count": len(skipped),
            "skipped_reasons": skipped_reasons,
        }

    # ========== 私有辅助方法 ==========

    async def _get_subject(self, subject_id: str) -> Subject:
        result = await self.db.execute(select(Subject).where(Subject.id == subject_id))
        subject = result.scalar_one_or_none()
        if not subject:
            raise ValueError(f"受试者 {subject_id} 不存在")
        return subject

    async def _get_project(self, project_id: str) -> Optional[Project]:
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def _get_run(self, run_id: str) -> ScreeningRun:
        result = await self.db.execute(select(ScreeningRun).where(ScreeningRun.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            raise ValueError(f"初筛任务 {run_id} 不存在")
        return run

    async def _check_files_parsed(self, subject_id: str) -> bool:
        from app.models.file import UploadedFile
        result = await self.db.execute(
            select(func.count()).select_from(UploadedFile).where(
                UploadedFile.subject_id == subject_id,
                UploadedFile.parse_status != "completed",
            )
        )
        unparsed = result.scalar() or 0
        return unparsed == 0

    async def _load_criteria(self, project_id: str) -> List[EligibilityCriterion]:
        result = await self.db.execute(
            select(EligibilityCriterion)
            .where(
                EligibilityCriterion.project_id == project_id,
                EligibilityCriterion.is_active == True,
            )
            .order_by(EligibilityCriterion.sort_order)
        )
        return list(result.scalars().all())

    async def _load_chunks(self, subject_id: str) -> List[DocumentChunk]:
        result = await self.db.execute(
            select(DocumentChunk).where(DocumentChunk.subject_id == subject_id)
            .order_by(DocumentChunk.page_no, DocumentChunk.chunk_index)
        )
        return list(result.scalars().all())
