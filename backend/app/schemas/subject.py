from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class SubjectCreate(BaseModel):
    """新增受试者请求"""
    subject_no: str = Field(..., min_length=1, max_length=64)
    site_name: Optional[str] = Field(None, max_length=256)
    gender: Optional[str] = Field(None, pattern="^(男|女)?$")
    age: Optional[int] = None
    birth_year: Optional[int] = None
    diagnosis: Optional[str] = Field(None, max_length=512)
    remark: Optional[str] = None


class SubjectUpdate(BaseModel):
    """更新受试者请求"""
    site_name: Optional[str] = Field(None, max_length=256)
    gender: Optional[str] = Field(None, pattern="^(男|女)?$")
    age: Optional[int] = None
    birth_year: Optional[int] = None
    diagnosis: Optional[str] = Field(None, max_length=512)
    remark: Optional[str] = None


class SubjectResponse(BaseModel):
    """受试者详情响应"""
    id: str
    project_id: str
    subject_no: str
    site_name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    birth_year: Optional[int] = None
    diagnosis: Optional[str] = None
    remark: Optional[str] = None
    material_count: int = 0
    screening_status: str
    overall_result: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubjectListResponse(BaseModel):
    """受试者列表响应"""
    items: List[SubjectResponse]
    total: int
    page: int
    page_size: int
