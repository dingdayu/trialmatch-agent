"""AI 初筛 Celery 任务 — 对应 Task 12.4"""

from app.tasks.parse_document import run_single_screening

# 重新导出
__all__ = ["run_single_screening"]
