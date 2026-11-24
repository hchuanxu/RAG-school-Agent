"""FAQ 管理路由。

- GET    /faq                  列表（支持 status 筛选）
- GET    /faq/{faq_id}         详情
- POST   /faq/generate         触发自动生成（管理员）
- PUT    /faq/{faq_id}         编辑（管理员）
- POST   /faq/{faq_id}/publish 发布（管理员）
- POST   /faq/{faq_id}/reject  拒绝（管理员）
- DELETE /faq/{faq_id}         删除（管理员）
"""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.services.faq_service import faq_service

router = APIRouter(prefix="/faq", tags=["FAQ管理"])


class FAQGenerateRequest(BaseModel):
    """FAQ 生成请求。"""

    threshold: int = Field(10, ge=1, le=1000, description="触发生成的最低提问次数")


class FAQRejectRequest(BaseModel):
    """FAQ 拒绝请求。"""

    reason: Optional[str] = Field(None, description="拒绝原因")


class FAQUpdateRequest(BaseModel):
    """FAQ 更新请求。"""

    question: Optional[str] = Field(None, max_length=512, description="问题文本")
    answer: Optional[str] = Field(None, description="答案文本")
    source_documents: Optional[list] = Field(None, description="来源文档列表")


@router.get("", summary="FAQ 列表")
async def list_faqs(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[dict]:
    """分页获取 FAQ 列表，支持按 status 筛选。"""
    return await faq_service.get_faq_list(db, status, page, page_size)


@router.get("/{faq_id}", summary="FAQ 详情")
async def get_faq(
    faq_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """获取 FAQ 详情。"""
    return await faq_service.get_faq(db, faq_id)


@router.post("/generate", summary="触发 FAQ 自动生成")
async def generate_faq(
    payload: FAQGenerateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> dict:
    """基于高频问题自动生成 FAQ（需要管理员权限）。"""
    return await faq_service.generate_faq(db, threshold=payload.threshold)


@router.put("/{faq_id}", summary="编辑 FAQ")
async def update_faq(
    faq_id: int,
    payload: FAQUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> dict:
    """编辑 FAQ 内容（需要管理员权限）。"""
    data = payload.model_dump(exclude_unset=True)
    return await faq_service.update_faq(db, faq_id, data)


@router.post("/{faq_id}/publish", summary="发布 FAQ")
async def publish_faq(
    faq_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
) -> dict:
    """发布 FAQ，同步写入 ChromaDB（需要管理员权限）。"""
    return await faq_service.publish_faq(db, faq_id, reviewer_id=admin.id)


@router.post("/{faq_id}/reject", summary="拒绝 FAQ")
async def reject_faq(
    faq_id: int,
    payload: FAQRejectRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> dict:
    """拒绝 FAQ（需要管理员权限）。"""
    return await faq_service.reject_faq(db, faq_id, reason=payload.reason)


@router.delete("/{faq_id}", summary="删除 FAQ")
async def delete_faq(
    faq_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> dict:
    """删除 FAQ 及其向量（需要管理员权限）。"""
    await faq_service.delete_faq(db, faq_id)
    return {"message": "FAQ 已删除", "faq_id": faq_id}
