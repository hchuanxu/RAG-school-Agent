"""全局依赖与启动辅助。

集中存放跨模块共享的依赖（如 OAuth2 令牌提取器的再导出）以及应用
初始化逻辑（建表与初始管理员创建）。
"""
from fastapi.security import OAuth2PasswordBearer

from app.config import settings

# OAuth2 令牌提取器（与认证服务保持一致的 tokenUrl）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# 默认管理员配置（与 user_service 保持一致，便于环境变量扩展）
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123456"


async def init_database() -> None:
    """应用启动时创建数据库表并初始化管理员账号。"""
    from app.db.base import Base
    from app.db.session import AsyncSessionLocal, engine
    # 导入所有模型以注册到 Base.metadata
    from app import models  # noqa: F401
    from app.services.user_service import user_service

    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 创建初始管理员
    async with AsyncSessionLocal() as session:
        await user_service.create_initial_admin(session)


__all__ = ["oauth2_scheme", "init_database", "settings"]
