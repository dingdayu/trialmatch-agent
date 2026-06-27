"""批量初筛 Celery 任务 — 对应 Task 12.5"""

from app.tasks.parse_document import run_batch_screening

__all__ = ["run_batch_screening"]
