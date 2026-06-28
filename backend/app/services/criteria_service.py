from __future__ import annotations

import os
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.criteria import EligibilityCriterion
from app.models.file import UploadedFile
from app.utils.logger import logger


class CriteriaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_criteria(
        self,
        project_id: str,
        criterion_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[EligibilityCriterion]:
        """获取项目入排标准列表"""
        query = select(EligibilityCriterion).where(
            EligibilityCriterion.project_id == project_id
        )

        if criterion_type:
            query = query.where(EligibilityCriterion.criterion_type == criterion_type)
        if is_active is not None:
            query = query.where(EligibilityCriterion.is_active == is_active)

        query = query.order_by(EligibilityCriterion.sort_order)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_criterion(self, criterion_id: str) -> EligibilityCriterion:
        """获取单条标准"""
        result = await self.db.execute(
            select(EligibilityCriterion).where(EligibilityCriterion.id == criterion_id)
        )
        criterion = result.scalar_one_or_none()
        if not criterion:
            raise ValueError(f"入排标准 {criterion_id} 不存在")
        return criterion

    async def create_criterion(self, project_id: str, data: dict) -> EligibilityCriterion:
        """新增入排标准"""
        # 检查编号是否在项目内重复
        existing = await self.db.execute(
            select(EligibilityCriterion).where(
                EligibilityCriterion.project_id == project_id,
                EligibilityCriterion.criterion_code == data["criterion_code"],
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"标准编号 {data['criterion_code']} 在当前项目中已存在")

        criterion = EligibilityCriterion(project_id=project_id, **data)
        self.db.add(criterion)
        await self.db.commit()
        await self.db.refresh(criterion)
        return criterion

    async def update_criterion(self, criterion_id: str, data: dict) -> EligibilityCriterion:
        """更新入排标准"""
        criterion = await self.get_criterion(criterion_id)
        for key, value in data.items():
            if value is not None and hasattr(criterion, key):
                setattr(criterion, key, value)
        await self.db.commit()
        await self.db.refresh(criterion)
        return criterion

    async def delete_criterion(self, criterion_id: str) -> None:
        """删除入排标准"""
        criterion = await self.get_criterion(criterion_id)
        # 检查是否有关联的匹配结果
        from app.models.evaluation import CriterionEvaluation
        result = await self.db.execute(
            select(func.count()).select_from(CriterionEvaluation).where(
                CriterionEvaluation.criterion_id == criterion_id
            )
        )
        count = result.scalar() or 0
        if count > 0:
            raise ValueError(f"该标准已有 {count} 条匹配结果，无法删除")
        await self.db.delete(criterion)
        await self.db.commit()

    async def generate_from_protocol(
        self, project_id: str, file_id: Optional[str] = None
    ) -> dict:
        """从研究方案文件解析并生成入排标准草稿（AI 生成，需人工确认）"""
        logger.info(
            f"[入排解析] 收到生成请求: project_id={project_id}, file_id={file_id or '(最新方案)'}"
        )
        protocol_file = await self._resolve_protocol_file(project_id, file_id)
        if not protocol_file:
            logger.warning(f"[入排解析] 项目 {project_id} 未找到研究方案文件")
            raise ValueError("未找到该项目的研究方案文件，请先上传方案")

        logger.info(
            f"[入排解析] 命中方案文件: id={protocol_file.id}, "
            f"name={protocol_file.file_name}, path={protocol_file.file_path}"
        )

        text_content, file_bytes, file_ext = self._load_protocol_payload(protocol_file)
        logger.info(
            f"[入排解析] 载荷加载: ext={file_ext}, "
            f"text={'有' if text_content else '无'}, "
            f"bytes={len(file_bytes) if file_bytes else 0}"
        )

        from app.agents import ProtocolParsingAgent

        agent = ProtocolParsingAgent()
        generated = await agent.parse(
            text_content=text_content,
            file_bytes=file_bytes,
            file_ext=file_ext,
        )

        if not generated:
            logger.warning(f"[入排解析] 项目 {project_id} 未生成任何入排标准")
            return {"generated_count": 0, "criteria": []}

        existing_codes = await self._existing_codes(project_id)
        next_inclusion = self._next_index(existing_codes, "I")
        next_exclusion = self._next_index(existing_codes, "E")

        created: List[EligibilityCriterion] = []
        for item in generated:
            ctype = "inclusion" if item.criterion_type == "inclusion" else "exclusion"
            if ctype == "inclusion":
                code = f"I-{next_inclusion:02d}"
                next_inclusion += 1
            else:
                code = f"E-{next_exclusion:02d}"
                next_exclusion += 1

            if code in existing_codes:
                continue
            existing_codes.add(code)

            criterion = EligibilityCriterion(
                project_id=project_id,
                criterion_code=code,
                criterion_type=ctype,
                criterion_text=item.criterion_text,
                criterion_explanation=item.criterion_explanation or None,
                ai_instruction=item.ai_instruction or None,
                required_fields=item.required_fields or [],
                sort_order=len(existing_codes),
                is_active=False,
                source="ai_generated",
                review_status="draft",
            )
            self.db.add(criterion)
            created.append(criterion)

        await self.db.commit()
        for c in created:
            await self.db.refresh(c)

        logger.info(
            f"[入排解析] 落库完成: 方案 {protocol_file.id} 生成草稿 {len(created)} 条 "
            f"(source=ai_generated, review_status=draft, is_active=False)"
        )
        return {"generated_count": len(created), "criteria": created}

    async def _resolve_protocol_file(
        self, project_id: str, file_id: Optional[str]
    ) -> Optional[UploadedFile]:
        query = select(UploadedFile).where(
            UploadedFile.project_id == project_id,
            UploadedFile.file_scope == "project_protocol",
        )
        if file_id:
            query = query.where(UploadedFile.id == file_id)
        else:
            query = query.order_by(UploadedFile.uploaded_at.desc())
        result = await self.db.execute(query.limit(1))
        return result.scalar_one_or_none()

    @staticmethod
    def _load_protocol_payload(protocol_file: UploadedFile):
        ext = os.path.splitext(protocol_file.file_name or "")[1].lower()
        if not os.path.exists(protocol_file.file_path):
            raise ValueError("研究方案文件已丢失，请重新上传")

        if ext in (".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"):
            with open(protocol_file.file_path, "rb") as f:
                return None, f.read(), ext

        with open(protocol_file.file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(), None, ext

    async def _existing_codes(self, project_id: str) -> set:
        result = await self.db.execute(
            select(EligibilityCriterion.criterion_code).where(
                EligibilityCriterion.project_id == project_id
            )
        )
        return {row[0] for row in result.all()}

    @staticmethod
    def _next_index(existing_codes: set, prefix: str) -> int:
        max_idx = 0
        for code in existing_codes:
            if code.startswith(f"{prefix}-"):
                try:
                    max_idx = max(max_idx, int(code.split("-")[1]))
                except (ValueError, IndexError):
                    continue
        return max_idx + 1

    async def batch_import(self, project_id: str, criteria_data: List[dict]) -> dict:
        """批量导入入排标准"""
        created = 0
        errors = []
        for item in criteria_data:
            try:
                await self.create_criterion(project_id, item)
                created += 1
            except ValueError as e:
                errors.append({"criterion_code": item.get("criterion_code"), "error": str(e)})
        return {"created_count": created, "failed_count": len(errors), "errors": errors}

    async def batch_update(self, project_id: str, action: str, ids: List[str],
                           sort_orders: Optional[List[int]] = None,
                           is_active: Optional[bool] = None) -> int:
        """批量操作入排标准 (reorder / toggle_active)"""
        count = 0
        for idx, criterion_id in enumerate(ids):
            criterion = await self.get_criterion(criterion_id)
            if criterion.project_id != project_id:
                continue
            if action == "reorder" and sort_orders:
                criterion.sort_order = sort_orders[idx] if idx < len(sort_orders) else idx
            elif action == "toggle_active":
                criterion.is_active = is_active if is_active is not None else not criterion.is_active
            count += 1
        await self.db.commit()
        return count
