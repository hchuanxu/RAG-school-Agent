"""数据库会话管理。

创建异步 engine 与 sessionmaker，并提供 get_db 依赖注入函数。
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# 创建异步 engine
# SQLite 需要启用 check_same_thread=False 以支持多线程/异步访问
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
    future=True,
)

# 创建异步 session 工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """异步数据库会话依赖注入。

    用法：
        @app.get("/")
        async def index(db: AsyncSession = Depends(get_db)):
            ...

    Yields:
        AsyncSession: 异步数据库会话。
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
