"""
TrialMatch AI API 路由汇总注册

将所有 v1 模块路由注册到统一的 router
"""

from fastapi import APIRouter

# 创建 v1 路由汇总器
api_v1_router = APIRouter(prefix="/api/v1")

# ============================================
# 注册各模块路由（后续 Task 逐步实现）
# ============================================

# Task 4: 认证模块
# from app.api.v1 import auth
# api_v1_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# Task 6: 项目管理模块
# from app.api.v1 import projects
# api_v1_router.include_router(projects.router, prefix="/projects", tags=["项目管理"])

# Task 7: 入排标准模块
# from app.api.v1 import criteria
# api_v1_router.include_router(criteria.router, tags=["入排标准"])

# Task 11: 受试者模块
# from app.api.v1 import subjects
# api_v1_router.include_router(subjects.router, tags=["受试者管理"])

# Task 8: 文件管理模块
# from app.api.v1 import files
# api_v1_router.include_router(files.router, tags=["文件管理"])

# Task 12: AI 初筛模块
# from app.api.v1 import screening
# api_v1_router.include_router(screening.router, tags=["AI初筛"])

# Task 13: 匹配结果模块
# from app.api.v1 import evaluations
# api_v1_router.include_router(evaluations.router, tags=["匹配结果"])

# Task 15: 导出模块
# from app.api.v1 import export
# api_v1_router.include_router(export.router, tags=["报告导出"])

# Task 16: 统计模块
# from app.api.v1 import dashboard
# api_v1_router.include_router(dashboard.router, tags=["项目统计"])

# Task 17: 审计日志模块
# from app.api.v1 import audit
# api_v1_router.include_router(audit.router, prefix="/audit-logs", tags=["审计日志"])

# Task 18: WebSocket 模块
# from app.api.v1 import ws
# api_v1_router.include_router(ws.router, tags=["WebSocket"])
