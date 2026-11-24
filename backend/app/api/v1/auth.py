"""认证路由。

- POST /login    登录
- POST /register 注册
- POST /guest    创建访客
- POST /refresh  刷新令牌
- GET  /me       获取当前用户
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


class RefreshRequest(BaseModel):
    """刷新令牌请求。"""

    refresh_token: str = Field(..., description="刷新令牌")


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(
    payload: LoginRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """使用用户名与密码登录，返回访问与刷新令牌。"""
    return await auth_service.login(db, payload.username, payload.password)


@router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(
    payload: RegisterRequest, db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """注册新用户。"""
    return await auth_service.register(
        db, payload.username, payload.email, payload.password
    )


@router.post("/guest", response_model=TokenResponse, summary="创建访客")
async def guest(db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """创建访客用户并签发令牌。"""
    return await auth_service.create_guest(db)


@router.post("/refresh", response_model=TokenResponse, summary="刷新令牌")
async def refresh(
    payload: RefreshRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """使用刷新令牌换取新的令牌对。"""
    return await auth_service.refresh_token(db, payload.refresh_token)


@router.get("/me", response_model=UserResponse, summary="获取当前用户")
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """获取当前登录用户信息。"""
    return UserResponse.model_validate(current_user)
