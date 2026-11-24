"""溯源路由。

- GET /{citation_id} 获取引用详情
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.citation import CitationResponse
from app.services.citation_service import citation_service

router = APIRouter(prefix="/citations", tags=["溯源"])


@router.get(
    "/{citation_id}", response_model=CitationResponse, summary="获取引用详情"
)
async def get_citation(
    citation_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CitationResponse:
    """根据引用唯一标识获取引用溯源详情。"""
    return await citation_service.get_citation(db, citation_id)
