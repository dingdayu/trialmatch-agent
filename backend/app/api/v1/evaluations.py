from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.evaluation import (
    EvaluationDetailResponse,
    ManualReviewRequest,
    BatchReviewRequest,
    CitationResponse,
)
from app.services.evaluation_service import EvaluationService
from app.services.audit_service import record_audit
from app.schemas.enums import ActionType, TargetType
from app.repositories.evaluation_repo import EvaluationRepository
from app.utils.response import APIResponse
from app.models.user import User

router = APIRouter()


@router.get("/subjects/{subject_id}/evaluations/latest")
async def get_latest_evaluations(
    subject_id: str,
    criterion_type: Optional[str] = None,
    ai_result: Optional[str] = None,
    review_status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取受试者最新匹配结果"""
    service = EvaluationService(db)
    result = await service.get_latest_evaluations(
        subject_id=subject_id,
        criterion_type=criterion_type,
        ai_result=ai_result,
        review_status=review_status,
    )
    if not result:
        return APIResponse.success(
            data={
                "run_id": None,
                "subject": None,
                "project": None,
                "summary": None,
                "evaluations": [],
            },
            message="该受试者尚未进行 AI 初筛",
        )
    return APIResponse.success(data=result)


@router.get("/evaluations/{evaluation_id}")
async def get_evaluation_detail(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单条匹配结果详情（含证据引用）"""
    service = EvaluationService(db)
    result = await service.get_evaluation_detail(evaluation_id)
    if not result:
        raise HTTPException(status_code=404, detail="匹配结果不存在")
    return APIResponse.success(data=result)


@router.put("/evaluations/{evaluation_id}/manual-review")
async def manual_review(
    evaluation_id: str,
    body: ManualReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """人工复核单条标准"""
    service = EvaluationService(db)
    try:
        evaluation = await service.manual_review(
            evaluation_id=evaluation_id,
            manual_result=body.manual_result,
            manual_comment=body.manual_comment,
            review_status=body.review_status,
            reviewer_id=current_user.id,
        )
        await record_audit(
            db,
            user_id=current_user.id,
            action_type=ActionType.MANUAL_REVIEW,
            target_type=TargetType.EVALUATION,
            target_id=evaluation_id,
            subject_id=evaluation.subject_id,
            after_value={
                "manual_result": body.manual_result,
                "review_status": body.review_status,
            },
        )
        return APIResponse.success(data={
            "evaluation_id": evaluation_id,
            "review_status": body.review_status,
        })
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/subjects/{subject_id}/evaluations/batch-review")
async def batch_review(
    subject_id: str,
    body: BatchReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量人工确认"""
    service = EvaluationService(db)
    count = await service.batch_review(
        evaluation_ids=body.evaluation_ids,
        manual_comment=body.manual_comment,
        reviewer_id=current_user.id,
    )
    await record_audit(
        db,
        user_id=current_user.id,
        action_type=ActionType.BATCH_REVIEW,
        target_type=TargetType.SUBJECT,
        target_id=subject_id,
        subject_id=subject_id,
        after_value={"reviewed_count": count, "evaluation_ids": body.evaluation_ids},
    )
    return APIResponse.success(data={"reviewed_count": count})


# ========== 引用来源 (Task 14) ==========

@router.get("/evaluations/{evaluation_id}/citations")
async def get_citations(
    evaluation_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """#43 获取评价的引用来源列表"""
    repo = EvaluationRepository(db)
    citations = await repo.get_citations(evaluation_id)

    total = len(citations)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = citations[start:end]

    return APIResponse.success(
        data={
            "items": [CitationResponse.model_validate(c).model_dump() for c in page_items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/citations/{citation_id}/context")
async def get_citation_context(
    citation_id: str,
    before: int = Query(1, ge=0, le=5),
    after: int = Query(1, ge=0, le=5),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """#44 查看引用原文上下文"""
    repo = EvaluationRepository(db)
    context = await repo.get_citation_context(citation_id, before=before, after=after)
    if not context:
        raise HTTPException(status_code=404, detail="引用不存在")
    return APIResponse.success(data=context)
