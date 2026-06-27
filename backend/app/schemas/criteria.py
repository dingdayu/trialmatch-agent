from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class CriteriaCreate(BaseModel):
    """新增入排标准请求"""
    criterion_code: str = Field(..., min_length=1, max_length=16)
    criterion_type: str = Field(..., pattern="^(inclusion|exclusion)$")
    criterion_text: str = Field(..., min_length=1)
    criterion_explanation: Optional[str] = None
    ai_instruction: Optional[str] = None
    required_fields: Optional[List[str]] = None
    sort_order: int = 0
    is_active: bool = True


class CriteriaUpdate(BaseModel):
    """更新入排标准请求"""
    criterion_code: Optional[str] = Field(None, max_length=16)
    criterion_text: Optional[str] = None
    criterion_explanation: Optional[str] = None
    ai_instruction: Optional[str] = None
    required_fields: Optional[List[str]] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class CriteriaResponse(BaseModel):
    """入排标准响应"""
    id: str
    project_id: str
    criterion_code: str
    criterion_type: str
    criterion_text: str
    criterion_explanation: Optional[str] = None
    ai_instruction: Optional[str] = None
    required_fields: Optional[List] = None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CriteriaBatchImport(BaseModel):
    """批量导入入排标准请求"""
    criteria: List[CriteriaCreate]


class CriteriaBatchUpdate(BaseModel):
    """批量操作入排标准请求 (reorder / toggle_active)"""
    action: str = Field(..., pattern="^(reorder|toggle_active)$")
    ids: List[str] = Field(..., min_length=1)
    # reorder 时的排序顺序
    sort_orders: Optional[List[int]] = None
    # toggle_active 时的目标状态
    is_active: Optional[bool] = None
