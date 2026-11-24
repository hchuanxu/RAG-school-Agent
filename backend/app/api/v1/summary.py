"""智能总结路由。

- GET    /summary/document/{doc_id}            获取文档总结
- POST   /summary/document/{doc_id}/regenerate 重新生成总结
- GET    /summary/document/{doc_id}/status     获取总结状态
- GET    /summary/document/{doc_id}/rules      获取条例
- GET    /summary/document/{doc_id}/questions  获取考点
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.summary_service import summary_service

router = APIRouter(prefix="/summary", tags=["智能总结"])


@router.get(
    "/document/{doc_id}",
    summary="获取文档总结",
)
async def get_summary(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """获取文档的摘要、关键条例与考点题目。"""
    return await summary_service.get_summary(db, doc_id)


@router.post(
    "/document/{doc_id}/regenerate",
    summary="重新生成总结",
)
async def regenerate_summary(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> dict:
    """重新生成文档的摘要、条例与考点（需要管理员权限）。"""
    return await summary_service.regenerate_summary(db, doc_id)


@router.get(
    "/document/{doc_id}/status",
    summary="获取总结状态",
)
async def get_summary_status(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """获取文档总结的处理状态：pending/processing/completed/failed。"""
    status = await summary_service.get_summary_status(db, doc_id)
    return {"document_id": doc_id, "summary_status": status}


@router.get(
    "/document/{doc_id}/rules",
    summary="获取关键条例",
)
async def get_key_rules(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """获取文档的关键条例列表。"""
    rules = await summary_service.get_key_rules(db, doc_id)
    return {"document_id": doc_id, "rules": rules, "total": len(rules)}


@router.get(
    "/document/{doc_id}/questions",
    summary="获取考点题目",
)
async def get_generated_questions(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """获取文档的考点题目列表。"""
    questions = await summary_service.get_generated_questions(db, doc_id)
    return {
        "document_id": doc_id,
        "questions": questions,
        "total": len(questions),
    }
