from __future__ import annotations

from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.criteria import EligibilityCriterion


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
        await self.db.delete(criterion)
        await self.db.commit()

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
