"""文档路由。

- GET    /{kb_id}/list             文档列表
- POST   /{kb_id}/upload           上传文档（管理员）
- GET    /doc/{doc_id}             文档详情
- DELETE /doc/{doc_id}             删除文档（管理员）
- POST   /doc/{doc_id}/reindex     重建索引（管理员）
- GET    /{kb_id}/processing-status 处理状态
"""
from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.document import DocumentResponse, DocumentUploadAck
from app.services.document_service import document_service

router = APIRouter(prefix="/documents", tags=["文档"])


@router.get(
    "/{kb_id}/list",
    response_model=PaginatedResponse[DocumentResponse],
    summary="文档列表",
)
async def list_documents(
    kb_id: int,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[DocumentResponse]:
    """分页获取指定知识库下的文档列表。"""
    return await document_service.list_documents(db, kb_id, page, page_size)


@router.post(
    "/{kb_id}/upload",
    response_model=DocumentUploadAck,
    summary="上传文档",
)
async def upload_document(
    kb_id: int,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> DocumentUploadAck:
    """上传文档并自动解析、切片、向量化、入库（需要管理员权限）。"""
    return await document_service.upload_document(db, kb_id, file)


@router.get(
    "/doc/{doc_id}",
    response_model=DocumentResponse,
    summary="文档详情",
)
async def get_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DocumentResponse:
    """获取文档详情。"""
    return await document_service.get_document(db, doc_id)


@router.delete("/doc/{doc_id}", summary="删除文档")
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> dict:
    """删除文档及其向量与磁盘文件（需要管理员权限）。"""
    await document_service.delete_document(db, doc_id)
    return {"message": "文档已删除", "document_id": doc_id}


@router.post(
    "/doc/{doc_id}/reindex",
    response_model=DocumentResponse,
    summary="重建索引",
)
async def reindex_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> DocumentResponse:
    """清除旧向量并重新解析、向量化入库（需要管理员权限）。"""
    return await document_service.reindex_document(db, doc_id)


@router.get(
    "/{kb_id}/processing-status", summary="文档处理状态"
)
async def processing_status(
    kb_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """获取知识库下文档处理状态汇总。"""
    return await document_service.get_processing_status(db, kb_id)
