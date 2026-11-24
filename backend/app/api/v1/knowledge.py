"""知识库路由。

- GET    /list           知识库列表
- POST   /create         创建知识库（管理员）
- GET    /{kb_id}        知识库详情
- PUT    /{kb_id}        更新知识库（管理员）
- DELETE /{kb_id}        删除知识库（管理员）
- GET    /{kb_id}/stats  知识库统计
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.knowledge import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)
from app.services.knowledge_service import knowledge_service

router = APIRouter(prefix="/knowledge", tags=["知识库"])


@router.get(
    "/list",
    response_model=PaginatedResponse[KnowledgeBaseResponse],
    summary="知识库列表",
)
async def list_knowledge_bases(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[KnowledgeBaseResponse]:
    """分页获取知识库列表。"""
    return await knowledge_service.list_knowledge_bases(db, page, page_size)


@router.post(
    "/create",
    response_model=KnowledgeBaseResponse,
    summary="创建知识库",
)
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> KnowledgeBaseResponse:
    """创建知识库（需要管理员权限）。"""
    return await knowledge_service.create_knowledge_base(
        db, payload.name, payload.description, payload.is_public
    )


@router.get(
    "/{kb_id}",
    response_model=KnowledgeBaseResponse,
    summary="知识库详情",
)
async def get_knowledge_base(
    kb_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> KnowledgeBaseResponse:
    """获取知识库详情。"""
    kb = await knowledge_service.get_knowledge_base(db, kb_id)
    return KnowledgeBaseResponse.model_validate(kb)


@router.put(
    "/{kb_id}",
    response_model=KnowledgeBaseResponse,
    summary="更新知识库",
)
async def update_knowledge_base(
    kb_id: int,
    payload: KnowledgeBaseUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> KnowledgeBaseResponse:
    """更新知识库信息（需要管理员权限）。"""
    return await knowledge_service.update_knowledge_base(db, kb_id, payload)


@router.delete("/{kb_id}", summary="删除知识库")
async def delete_knowledge_base(
    kb_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> dict:
    """删除知识库及其关联文档与向量（需要管理员权限）。"""
    await knowledge_service.delete_knowledge_base(db, kb_id)
    return {"message": "知识库已删除", "knowledge_base_id": kb_id}


@router.get("/{kb_id}/stats", summary="知识库统计")
async def knowledge_base_stats(
    kb_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """获取知识库文档与向量统计。"""
    return await knowledge_service.get_knowledge_base_stats(db, kb_id)
