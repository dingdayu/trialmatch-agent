from fastapi import APIRouter
from app.api.v1 import auth, projects, criteria, subjects, files, evaluations

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router, prefix="/auth", tags=["认证"])
router.include_router(projects.router, prefix="/projects", tags=["项目"])
router.include_router(criteria.router, tags=["入排标准"])
router.include_router(subjects.router, tags=["受试者"])
router.include_router(files.router, prefix="/files", tags=["文件"])
router.include_router(evaluations.router, tags=["匹配结果"])
