"""导出服务 — 对应 Task 15.1"""

from __future__ import annotations

import json
import uuid
import os
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.models.subject import Subject
from app.models.project import Project
from app.models.evaluation import CriterionEvaluation
from app.models.citation import EvaluationCitation
from app.models.screening_run import ScreeningRun

settings = get_settings()


class ExportService:
    """报告导出服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_export_task(self, subject_id: str, format: str = "json") -> dict:
        """创建导出任务"""
        subject = await self._get_subject(subject_id)

        task_id = str(uuid.uuid4())
        export_dir = os.path.join(settings.upload_dir, "exports")
        os.makedirs(export_dir, exist_ok=True)

        return {
            "export_task_id": task_id,
            "subject_id": subject_id,
            "format": format,
            "status": "queued",
            "message": "导出任务已创建",
        }

    async def generate_report(self, subject_id: str, task_id: str, format: str = "json") -> str:
        """生成导出报告，返回文件路径"""
        subject = await self._get_subject(subject_id)
        project = await self._get_project(subject.project_id)

        # 获取最新匹配结果
        run_result = await self.db.execute(
            select(ScreeningRun)
            .where(ScreeningRun.subject_id == subject_id, ScreeningRun.status == "completed")
            .order_by(ScreeningRun.completed_at.desc())
            .limit(1)
        )
        latest_run = run_result.scalar_one_or_none()

        evaluations = []
        summary = None
        if latest_run:
            ev_result = await self.db.execute(
                select(CriterionEvaluation).where(CriterionEvaluation.run_id == latest_run.id)
            )
            ev_list = list(ev_result.scalars().all())

            for ev in ev_list:
                cit_result = await self.db.execute(
                    select(EvaluationCitation).where(EvaluationCitation.evaluation_id == ev.id)
                )
                citations = list(cit_result.scalars().all())

                evaluations.append({
                    "criterion_code": ev.criterion_code,
                    "criterion_type": ev.criterion_type,
                    "criterion_text": ev.criterion_text,
                    "ai_result": ev.ai_result,
                    "confidence_score": ev.confidence_score,
                    "ai_rationale": ev.ai_rationale,
                    "manual_result": ev.manual_result,
                    "review_status": ev.review_status,
                    "citations": [
                        {
                            "quoted_text": c.quoted_text,
                            "extracted_fact": c.extracted_fact,
                            "relevance_explanation": c.relevance_explanation,
                        }
                        for c in citations
                    ],
                })

            from app.services.ai_engine import AIEngine
            summary = {
                "overall_result": AIEngine.compute_overall_result(ev_list),
                "overall_score": AIEngine.compute_overall_score(ev_list),
            }

        report = {
            "task_id": task_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "subject": {
                "subject_no": subject.subject_no,
                "site_name": subject.site_name,
                "gender": subject.gender,
                "age": subject.age,
                "diagnosis": subject.diagnosis,
            },
            "project": {
                "project_no": project.project_no if project else "",
                "study_name": project.study_name if project else "",
                "indication": project.indication if project else "",
            } if project else None,
            "summary": summary,
            "evaluations": evaluations,
        }

        # 写入文件
        export_dir = os.path.join(settings.upload_dir, "exports")
        os.makedirs(export_dir, exist_ok=True)

        if format == "json":
            file_path = os.path.join(export_dir, f"{task_id}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        else:
            # 默认 JSON
            file_path = os.path.join(export_dir, f"{task_id}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        return file_path

    async def get_export_status(self, task_id: str) -> dict:
        """获取导出任务状态"""
        export_dir = os.path.join(settings.upload_dir, "exports")
        file_path = os.path.join(export_dir, f"{task_id}.json")

        if os.path.exists(file_path):
            return {
                "task_id": task_id,
                "status": "completed",
                "download_url": f"/api/v1/export-tasks/{task_id}/download",
            }
        return {
            "task_id": task_id,
            "status": "processing",
            "download_url": None,
        }

    async def _get_subject(self, subject_id: str) -> Subject:
        result = await self.db.execute(select(Subject).where(Subject.id == subject_id))
        subject = result.scalar_one_or_none()
        if not subject:
            raise ValueError(f"受试者 {subject_id} 不存在")
        return subject

    async def _get_project(self, project_id: str) -> Optional[Project]:
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()
