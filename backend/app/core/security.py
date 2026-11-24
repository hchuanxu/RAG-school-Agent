"""安全工具模块。

提供 JWT 令牌生成与校验、密码哈希与校验功能。
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
from jose import JWTError, jwt

from app.config import settings


def get_password_hash(password: str) -> str:
    """对明文密码进行 bcrypt 哈希处理。

    Args:
        password: 明文密码。

    Returns:
        哈希后的密码字符串。
    """
    # bcrypt 限制 72 字节，截断处理避免 ValueError
    pw_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希密码是否匹配。

    Args:
        plain_password: 明文密码。
        hashed_password: 哈希后的密码。

    Returns:
        匹配返回 True，否则返回 False。
    """
    try:
        pw_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except (ValueError, TypeError):
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """生成访问令牌（JWT）。

    Args:
        data: 需要编码到 token 中的数据，通常包含 sub（用户标识）。
        expires_delta: 自定义过期时长，未提供则使用默认配置。

    Returns:
        编码后的 JWT 字符串。
    """
    to_encode: Dict[str, Any] = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """生成刷新令牌（JWT）。

    Args:
        data: 需要编码到 token 中的数据。
        expires_delta: 自定义过期时长，未提供则使用默认配置。

    Returns:
        编码后的 JWT 字符串。
    """
    to_encode: Dict[str, Any] = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )


def verify_token(token: str) -> dict:
    """校验 JWT 令牌并返回其中的 payload。

    Args:
        token: 待校验的 JWT 字符串。

    Returns:
        解码后的 payload 字典。

    Raises:
        JWTError: 当 token 无效或已过期时抛出。
    """
    try:
        payload: dict = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise
