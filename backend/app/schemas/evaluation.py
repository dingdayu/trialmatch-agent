from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class CitationResponse(BaseModel):
    """证据引用响应"""
    id: str
    file_id: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    page_no: Optional[int] = None
    chunk_id: Optional[str] = None
    quoted_text: Optional[str] = None
    extracted_fact: Optional[str] = None
    relevance_explanation: Optional[str] = None

    class Config:
        from_attributes = True


class EvaluationItemResponse(BaseModel):
    """匹配结果列表项"""
    id: str
    criterion_id: str
    criterion_code: str
    criterion_type: str
    criterion_text: str
    ai_result: str
    confidence_score: Optional[int] = None
    ai_rationale: Optional[str] = None
    citation_count: int = 0
    manual_result: Optional[str] = None
    manual_comment: Optional[str] = None
    review_status: str

    class Config:
        from_attributes = True


class EvaluationDetailResponse(BaseModel):
    """单条匹配结果详情（含证据引用）"""
    id: str
    run_id: str
    project_id: str
    subject_id: str
    criterion_id: str
    criterion_code: str
    criterion_type: str
    criterion_text: str
    criterion_explanation: Optional[str] = None
    ai_result: str
    confidence_score: Optional[int] = None
    ai_rationale: Optional[str] = None
    manual_result: Optional[str] = None
    manual_comment: Optional[str] = None
    review_status: str
    reviewer_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    citations: List[CitationResponse] = []

    class Config:
        from_attributes = True


class EvaluationSummary(BaseModel):
    """初筛汇总"""
    overall_result: Optional[str] = None
    score: Optional[int] = None
    ai_advice: Optional[str] = None
    inclusion_pass_count: int = 0
    inclusion_fail_count: int = 0
    inclusion_insufficient_count: int = 0
    exclusion_hit_count: int = 0
    exclusion_not_hit_count: int = 0
    manual_review_count: int = 0


class EvaluationListResponse(BaseModel):
    """受试者最新匹配结果响应"""
    run_id: str
    subject: dict
    project: dict
    summary: EvaluationSummary
    evaluations: List[EvaluationItemResponse]


class ManualReviewRequest(BaseModel):
    """人工复核请求"""
    manual_result: str = Field(..., pattern="^(pass|fail|exclusion_hit|exclusion_not_hit|insufficient_data|manual_review)$")
    manual_comment: Optional[str] = None
    review_status: str = Field(default="reviewed", pattern="^(reviewed|modified)$")


class BatchReviewRequest(BaseModel):
    """批量人工确认请求"""
    evaluation_ids: List[str]
    manual_comment: Optional[str] = None
