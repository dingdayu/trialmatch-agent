"""AI 初筛模块 Schema — 对应 Task 12.1"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class ScreeningRunRequest(BaseModel):
    """启动单个 AI 初筛请求"""
    model_name: Optional[str] = Field(None, description="指定模型名称")
    prompt_version: Optional[str] = Field(None, description="提示词版本")
    criteria_ids: Optional[List[str]] = Field(None, description="指定标准子集")
    force_reparse_files: bool = Field(default=False, description="强制重新解析文件")


class BatchRunRequest(BaseModel):
    """批量启动 AI 初筛请求"""
    subject_ids: List[str] = Field(..., min_length=1, description="受试者 ID 列表")
    model_name: Optional[str] = None
    prompt_version: Optional[str] = None
    criteria_ids: Optional[List[str]] = None
    force_reparse_files: bool = False


class ScreeningRunResponse(BaseModel):
    """初筛任务响应"""
    id: str
    project_id: str
    subject_id: str
    run_no: str
    status: str
    model_name: Optional[str] = None
    prompt_version: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ScreeningRunListItem(BaseModel):
    """初筛任务列表项"""
    id: str
    subject_id: str
    run_no: str
    status: str
    model_name: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ScreeningRunDetail(BaseModel):
    """初筛任务详情（含 summary）"""
    id: str
    project_id: str
    subject_id: str
    run_no: str
    status: str
    model_name: Optional[str] = None
    prompt_version: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    summary: Optional[dict] = None

    class Config:
        from_attributes = True


class RerunRequest(BaseModel):
    """重新运行初筛请求"""
    model_name: Optional[str] = None
    prompt_version: Optional[str] = None
    criteria_ids: Optional[List[str]] = None


class ConfirmAllResponse(BaseModel):
    """确认全部响应"""
    confirmed_count: int
    subject_id: str
    new_status: str


class BatchRunResponse(BaseModel):
    """批量启动响应"""
    batch_id: str
    runs: List[ScreeningRunResponse]
    skipped_count: int
    skipped_reasons: List[str] = []
