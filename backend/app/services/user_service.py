"""用户服务。

提供用户查询、更新、分页列表与初始管理员创建等功能。
"""
from typing import Optional

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException, ResourceNotFoundError
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.common import PaginatedResponse

# 初始管理员默认配置（生产环境请通过环境变量覆盖或登录后修改）
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_EMAIL = "admin@campus.edu"
DEFAULT_ADMIN_PASSWORD = "admin123456"


class UserService:
    """用户服务。"""

    async def get_user_by_id(
        self, db: AsyncSession, user_id: int
    ) -> User:
        """根据 ID 获取用户。"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise ResourceNotFoundError("用户不存在")
        return user

    async def get_user_by_username(
        self, db: AsyncSession, username: str
    ) -> Optional[User]:
        """根据用户名获取用户。"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def update_user(
        self, db: AsyncSession, user_id: int, data: dict
    ) -> UserResponse:
        """更新用户信息。

        Args:
            db: 异步数据库会话。
            user_id: 用户ID。
            data: 待更新字段，支持 email / password。

        Returns:
            更新后的用户信息。
        """
        user = await self.get_user_by_id(db, user_id)

        email = data.get("email")
        if email is not None:
            # 校验邮箱唯一
            existing = await db.execute(
                select(User).where(User.email == email, User.id != user_id)
            )
            if existing.scalar_one_or_none() is not None:
                raise BusinessException(code=409, message="邮箱已被占用")
            user.email = email

        password = data.get("password")
        if password is not None:
            if len(password) < 6:
                raise BusinessException(code=400, message="密码长度至少6位")
            user.hashed_password = get_password_hash(password)

        await db.commit()
        await db.refresh(user)
        logger.info(f"用户信息已更新: user_id={user_id}")
        return UserResponse.model_validate(user)

    async def get_users(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
    ) -> PaginatedResponse[UserResponse]:
        """分页获取用户列表，支持关键词搜索。"""
        page = max(page, 1)
        page_size = max(min(page_size, 100), 1)

        # 基础查询
        stmt = select(User)
        count_stmt = select(func.count(User.id))
        if keyword:
            like_pattern = f"%{keyword}%"
            stmt = stmt.where(
                (User.username.ilike(like_pattern))
                | (User.email.ilike(like_pattern))
            )
            count_stmt = count_stmt.where(
                (User.username.ilike(like_pattern))
                | (User.email.ilike(like_pattern))
            )

        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        result = await db.execute(
            stmt.order_by(User.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        users = result.scalars().all()

        total_pages = (total + page_size - 1) // page_size if total else 0
        return PaginatedResponse[UserResponse](
            items=[UserResponse.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_user_role(
        self, db: AsyncSession, user_id: int, role: str
    ) -> UserResponse:
        """更新用户角色。"""
        if role not in ("user", "admin"):
            raise BusinessException(code=400, message="角色必须为 user 或 admin")
        user = await self.get_user_by_id(db, user_id)
        user.role = role
        await db.commit()
        await db.refresh(user)
        logger.info(f"用户角色已更新: user_id={user_id}, role={role}")
        return UserResponse.model_validate(user)

    async def update_user_status(
        self, db: AsyncSession, user_id: int, is_active: bool
    ) -> UserResponse:
        """启用/禁用用户。"""
        user = await self.get_user_by_id(db, user_id)
        user.is_active = is_active
        await db.commit()
        await db.refresh(user)
        logger.info(f"用户状态已更新: user_id={user_id}, is_active={is_active}")
        return UserResponse.model_validate(user)

    async def create_initial_admin(self, db: AsyncSession) -> Optional[User]:
        """创建初始管理员账号。

        当系统中不存在任何用户时，创建默认管理员。

        Returns:
            新创建的管理员用户，若已存在用户则返回 None。
        """
        count_result = await db.execute(select(func.count(User.id)))
        user_count = count_result.scalar_one()
        if user_count > 0:
            return None

        admin = User(
            username=DEFAULT_ADMIN_USERNAME,
            email=DEFAULT_ADMIN_EMAIL,
            hashed_password=get_password_hash(DEFAULT_ADMIN_PASSWORD),
            role="admin",
            is_active=True,
            is_guest=False,
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        logger.warning(
            f"初始管理员已创建: username={DEFAULT_ADMIN_USERNAME}, "
            f"password={DEFAULT_ADMIN_PASSWORD}（请尽快修改默认密码）"
        )
        return admin


# 模块级单例
user_service = UserService()
