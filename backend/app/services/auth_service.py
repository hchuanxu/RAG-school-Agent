"""认证服务。

封装登录、注册、访客创建、令牌刷新与当前用户加载等认证逻辑。
"""
from uuid import uuid4

from jose import JWTError
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthenticationError,
    BusinessException,
    PermissionDeniedError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.models.user import User
from app.schemas.auth import TokenResponse, UserResponse


class AuthService:
    """认证服务。"""

    async def login(
        self, db: AsyncSession, username: str, password: str
    ) -> TokenResponse:
        """用户名密码登录。

        Args:
            db: 异步数据库会话。
            username: 用户名。
            password: 明文密码。

        Returns:
            令牌响应。

        Raises:
            AuthenticationError: 用户名或密码错误，或账号已禁用。
        """
        logger.info(f"用户登录: username={username}")
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if user is None or not verify_password(password, user.hashed_password):
            logger.warning(f"登录失败，凭证无效: username={username}")
            raise AuthenticationError("用户名或密码错误")
        if not user.is_active:
            logger.warning(f"登录失败，账号已禁用: username={username}")
            raise AuthenticationError("账号已被禁用")

        return await self._issue_tokens(user)

    async def register(
        self,
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
    ) -> UserResponse:
        """用户注册。

        Args:
            db: 异步数据库会话。
            username: 用户名。
            email: 邮箱。
            password: 明文密码。

        Returns:
            新用户信息。

        Raises:
            BusinessException: 用户名或邮箱已存在。
        """
        logger.info(f"用户注册: username={username}, email={email}")

        existing = await db.execute(
            select(User).where(
                (User.username == username) | (User.email == email)
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise BusinessException(code=409, message="用户名或邮箱已存在")

        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            role="user",
            is_active=True,
            is_guest=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"注册成功: user_id={user.id}")
        return UserResponse.model_validate(user)

    async def create_guest(self, db: AsyncSession) -> TokenResponse:
        """创建访客用户并签发令牌。

        Args:
            db: 异步数据库会话。

        Returns:
            访客令牌响应。
        """
        username = f"guest_{uuid4().hex[:12]}"
        email = f"{username}@guest.local"
        # 访客使用随机密码（仅哈希存储，不对外返回）
        random_password = uuid4().hex
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(random_password),
            role="user",
            is_active=True,
            is_guest=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"访客用户已创建: user_id={user.id}, username={username}")
        return await self._issue_tokens(user)

    async def refresh_token(
        self, db: AsyncSession, refresh_token: str
    ) -> TokenResponse:
        """使用刷新令牌换取新的令牌对。

        Args:
            db: 异步数据库会话。
            refresh_token: 刷新令牌。

        Returns:
            新的令牌响应。

        Raises:
            AuthenticationError: 令牌无效或类型不正确。
        """
        try:
            payload = verify_token(refresh_token)
        except JWTError:
            raise AuthenticationError("刷新令牌无效或已过期")

        if payload.get("type") != "refresh":
            raise AuthenticationError("令牌类型不正确")

        sub = payload.get("sub")
        if sub is None:
            raise AuthenticationError("令牌载荷缺失")

        result = await db.execute(select(User).where(User.id == int(sub)))
        user = result.scalar_one_or_none()
        if user is None:
            raise AuthenticationError("用户不存在")
        if not user.is_active:
            raise AuthenticationError("账号已被禁用")

        logger.info(f"刷新令牌: user_id={user.id}")
        return await self._issue_tokens(user)

    async def get_current_user(
        self, db: AsyncSession, token: str
    ) -> User:
        """根据访问令牌加载当前用户。

        Args:
            db: 异步数据库会话。
            token: 访问令牌。

        Returns:
            当前用户对象。

        Raises:
            AuthenticationError: 令牌无效或用户不存在。
        """
        try:
            payload = verify_token(token)
        except JWTError:
            raise AuthenticationError("访问令牌无效或已过期")

        if payload.get("type") != "access":
            raise AuthenticationError("令牌类型不正确")

        sub = payload.get("sub")
        if sub is None:
            raise AuthenticationError("令牌载荷缺失")

        result = await db.execute(select(User).where(User.id == int(sub)))
        user = result.scalar_one_or_none()
        if user is None:
            raise AuthenticationError("用户不存在")
        if not user.is_active:
            raise AuthenticationError("账号已被禁用")
        return user

    async def _issue_tokens(self, user: User) -> TokenResponse:
        """为用户签发访问与刷新令牌。"""
        token_data = {"sub": str(user.id)}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )


# 模块级单例
auth_service = AuthService()


async def require_admin(user: User) -> User:
    """校验用户是否为管理员。"""
    if user.role != "admin":
        raise PermissionDeniedError("需要管理员权限")
    return user


__all__ = ["AuthService", "auth_service", "require_admin"]
