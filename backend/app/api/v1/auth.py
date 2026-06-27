from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.user import UserLogin, TokenResponse, UserResponse, ChangePasswordRequest
from app.services.auth_service import AuthService
from app.utils.response import APIResponse
from app.exceptions import UnauthorizedException, ForbiddenException, BadRequestException
from app.models.user import User
from app.utils.logger import logger

router = APIRouter()


@router.post("/login")
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    service = AuthService(db)
    try:
        result = await service.login(body.username, body.password)
        logger.info("用户登录成功", extra={"username": body.username})
        return APIResponse.success(data=result)
    except ValueError as e:
        raise UnauthorizedException(str(e))
    except PermissionError as e:
        raise ForbiddenException(str(e))


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return APIResponse.success(
        data={
            "id": current_user.id,
            "username": current_user.username,
            "display_name": current_user.display_name,
            "role": current_user.role,
            "email": current_user.email,
            "status": current_user.status,
        }
    )


@router.post("/refresh")
async def refresh_token(body: dict, db: AsyncSession = Depends(get_db)):
    """刷新访问令牌"""
    service = AuthService(db)
    try:
        result = await service.refresh_token(body.get("refresh_token", ""))
        return APIResponse.success(data=result)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """退出登录"""
    logger.info("用户退出登录", extra={"user_id": current_user.id})
    return APIResponse.success(data=True, message="已退出登录")


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改密码"""
    service = AuthService(db)
    try:
        await service.change_password(
            user_id=current_user.id,
            old_password=body.old_password,
            new_password=body.new_password,
        )
        logger.info("密码修改成功", extra={"user_id": current_user.id})
        return APIResponse.success(data=True, message="密码修改成功")
    except ValueError as e:
        raise BadRequestException(str(e))
