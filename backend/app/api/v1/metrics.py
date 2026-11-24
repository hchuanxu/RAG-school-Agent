"""评价指标路由。

- GET /metrics/overview    指标总览
- GET /metrics/retrieval   检索质量指标
- GET /metrics/answer      回答质量指标
- GET /metrics/latency     性能延迟指标
- GET /metrics/trends      指标趋势序列
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_db
from app.models.user import User
from app.services.metrics_service import metrics_service

router = APIRouter(prefix="/metrics", tags=["评价指标"])


@router.get("/overview", summary="指标总览")
async def overview(
    period: str = "week",
    knowledge_base_id: Optional[int] = Query(None, description="知识库 ID，可选筛选"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> dict:
    """返回四维度指标汇总概览（检索/回答/性能/业务）。"""
    return await metrics_service.get_overview(db, period, knowledge_base_id)


@router.get("/retrieval", summary="检索质量指标")
async def retrieval_metrics(
    period: str = "week",
    knowledge_base_id: Optional[int] = Query(None, description="知识库 ID，可选筛选"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> dict:
    """返回检索质量指标详情（命中率/MRR/召回数/耗时）。"""
    return await metrics_service.get_retrieval_metrics(db, period, knowledge_base_id)


@router.get("/answer", summary="回答质量指标")
async def answer_metrics(
    period: str = "week",
    knowledge_base_id: Optional[int] = Query(None, description="知识库 ID，可选筛选"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> dict:
    """返回回答质量指标详情（引用率/点踩率/幻觉率）。"""
    return await metrics_service.get_answer_metrics(db, period, knowledge_base_id)


@router.get("/latency", summary="性能延迟指标")
async def latency_metrics(
    period: str = "week",
    knowledge_base_id: Optional[int] = Query(None, description="知识库 ID，可选筛选"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> dict:
    """返回性能延迟指标详情（TTFT/P95/QPM）。"""
    return await metrics_service.get_latency_metrics(db, period, knowledge_base_id)


@router.get("/trends", summary="指标趋势序列")
async def trends(
    metric_type: str = "latency",
    period: str = "week",
    knowledge_base_id: Optional[int] = Query(None, description="知识库 ID，可选筛选"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> dict:
    """返回指定指标类型的时序数据。

    - metric_type: latency / retrieval / answer
    - period: day / week / month / all
    """
    return await metrics_service.get_metrics_trends(
        db, period, metric_type, knowledge_base_id
    )
