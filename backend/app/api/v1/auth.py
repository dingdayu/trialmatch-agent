from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.user import UserLogin, TokenResponse, UserResponse
from app.services.auth_service import AuthService
from app.utils.response import APIResponse
from app.models.user import User

router = APIRouter()


@router.post("/login")
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    service = AuthService(db)
    try:
        result = await service.login(body.username, body.password)
        return APIResponse.success(data=result)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


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
    return APIResponse.success(data=True, message="已退出登录")
