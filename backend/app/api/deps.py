"""API 公共依赖。

提供当前用户与管理员用户的依赖注入函数。
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedError
from app.db.session import get_db
from app.dependencies import oauth2_scheme
from app.models.user import User
from app.services.auth_service import auth_service


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从请求头解析并校验访问令牌，返回当前用户。"""
    return await auth_service.get_current_user(db, token)


async def get_admin_user(
    user: User = Depends(get_current_user),
) -> User:
    """校验当前用户为管理员，否则抛出 403。"""
    if user.role != "admin":
        raise PermissionDeniedError("需要管理员权限")
    return user


__all__ = ["get_current_user", "get_admin_user", "get_db"]
