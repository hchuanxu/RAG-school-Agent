"""用户路由。

- GET /profile 获取当前用户资料
- PUT /profile 更新当前用户资料
- GET /          用户列表（管理员）
- PUT /{id}/role 更新用户角色（管理员）
- PUT /{id}/status 启用/禁用用户（管理员）
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.common import PaginatedResponse
from app.services.user_service import user_service

router = APIRouter(prefix="/user", tags=["用户"])


class UpdateProfileRequest(BaseModel):
    """更新用户资料请求。"""

    email: Optional[str] = Field(None, description="新邮箱")
    password: Optional[str] = Field(None, description="新密码")


class UpdateRoleRequest(BaseModel):
    """更新用户角色请求。"""

    role: str = Field(..., description="角色：user/admin")


class UpdateStatusRequest(BaseModel):
    """更新用户状态请求。"""

    is_active: bool = Field(..., description="是否启用")


@router.get("/profile", response_model=UserResponse, summary="获取个人资料")
async def get_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """获取当前用户资料。"""
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse, summary="更新个人资料")
async def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """更新当前用户邮箱或密码。"""
    return await user_service.update_user(
        db, current_user.id, payload.model_dump(exclude_unset=True)
    )


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    summary="用户列表（管理员）",
)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None, description="搜索用户名或邮箱"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> PaginatedResponse[UserResponse]:
    """分页获取用户列表，支持关键词搜索（需要管理员权限）。"""
    return await user_service.get_users(db, page, page_size, keyword)


@router.put(
    "/{user_id}/role",
    response_model=UserResponse,
    summary="更新用户角色（管理员）",
)
async def update_user_role(
    user_id: int,
    payload: UpdateRoleRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
) -> UserResponse:
    """更新用户角色（需要管理员权限）。"""
    if user_id == admin.id:
        from app.core.exceptions import BusinessException

        raise BusinessException(code=400, message="不能修改自己的角色")
    return await user_service.update_user_role(db, user_id, payload.role)


@router.put(
    "/{user_id}/status",
    response_model=UserResponse,
    summary="启用/禁用用户（管理员）",
)
async def update_user_status(
    user_id: int,
    payload: UpdateStatusRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
) -> UserResponse:
    """启用或禁用用户（需要管理员权限）。"""
    if user_id == admin.id:
        from app.core.exceptions import BusinessException

        raise BusinessException(code=400, message="不能修改自己的状态")
    return await user_service.update_user_status(db, user_id, payload.is_active)
