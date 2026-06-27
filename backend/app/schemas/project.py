from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """创建项目请求"""
    project_no: str = Field(..., min_length=1, max_length=64)
    study_name: str = Field(..., min_length=1, max_length=512)
    study_short_name: Optional[str] = Field(None, max_length=256)
    indication: Optional[str] = Field(None, max_length=256)
    phase: Optional[str] = Field(None, max_length=64)
    sponsor: Optional[str] = Field(None, max_length=256)
    principal_investigator: Optional[str] = Field(None, max_length=256)
    project_manager: Optional[str] = Field(None, max_length=256)
    status: str = "draft"
    description: Optional[str] = None
    ai_prompt: Optional[str] = None


class ProjectUpdate(BaseModel):
    """更新项目请求"""
    study_name: Optional[str] = Field(None, max_length=512)
    study_short_name: Optional[str] = Field(None, max_length=256)
    indication: Optional[str] = Field(None, max_length=256)
    phase: Optional[str] = Field(None, max_length=64)
    sponsor: Optional[str] = Field(None, max_length=256)
    principal_investigator: Optional[str] = Field(None, max_length=256)
    project_manager: Optional[str] = Field(None, max_length=256)
    status: Optional[str] = None
    description: Optional[str] = None
    ai_prompt: Optional[str] = None


class ProjectResponse(BaseModel):
    """项目详情响应"""
    id: str
    project_no: str
    study_name: str
    study_short_name: Optional[str] = None
    indication: Optional[str] = None
    phase: Optional[str] = None
    sponsor: Optional[str] = None
    principal_investigator: Optional[str] = None
    project_manager: Optional[str] = None
    status: str
    description: Optional[str] = None
    ai_prompt: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """项目列表响应"""
    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int
