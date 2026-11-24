"""FastAPI 应用入口。

负责创建应用实例、配置 CORS、注册路由与异常处理器，并在启动时
初始化日志、数据库表与初始管理员。
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.citation import router as citation_router
from app.api.v1.document import router as document_router
from app.api.v1.faq import router as faq_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.stats import router as stats_router
from app.api.v1.summary import router as summary_router
from app.api.v1.user import router as user_router
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.dependencies import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化，关闭时清理。"""
    setup_logging()
    logger.info("应用启动中: {}", settings.APP_NAME)
    try:
        await init_database()
        logger.info("数据库表与初始管理员已就绪")
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"启动初始化失败: {exc}")
    logger.info("应用启动完成")
    yield
    logger.info("应用关闭")


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例。"""
    app = FastAPI(
        title=settings.APP_NAME,
        description="基于 RAG 与多智能体的校园知识库智能问答后端",
        version="1.0.0",
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(user_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(knowledge_router, prefix="/api/v1")
    app.include_router(document_router, prefix="/api/v1")
    app.include_router(citation_router, prefix="/api/v1")
    app.include_router(stats_router, prefix="/api/v1")
    app.include_router(summary_router, prefix="/api/v1")
    app.include_router(faq_router, prefix="/api/v1")
    app.include_router(analytics_router, prefix="/api/v1")
    app.include_router(metrics_router, prefix="/api/v1")

    # 全局异常处理器
    register_exception_handlers(app)

    # 健康检查
    @app.get("/health", tags=["系统"], summary="健康检查")
    async def health() -> dict:
        return {"status": "ok", "app": settings.APP_NAME}

    return app


app = create_app()
