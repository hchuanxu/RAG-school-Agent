"""统计分析路由。

- GET  /analytics/hot-questions        热门问题（period 参数）
- GET  /analytics/trends               趋势数据（type 参数：daily/weekly/monthly）
- GET  /analytics/intent-distribution  意图分布
- GET  /analytics/invalid-analysis     无效问题分析
- POST /analytics/refresh              手动刷新（占位接口）
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.analytics.question_analyzer import question_analyzer
from app.analytics.trend_calculator import trend_calculator

router = APIRouter(prefix="/analytics", tags=["统计分析"])


@router.get("/hot-questions", summary="热门问题")
async def hot_questions(
    period: str = "week",
    top_k: int = 10,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """获取热门问题列表。

    - period: day/week/month/all，默认 week。
    - top_k: 返回前 N 条，默认 10。
    """
    items = await question_analyzer.get_hot_questions(db, period, top_k)
    return {"period": period, "total": len(items), "items": items}


@router.get("/trends", summary="趋势数据")
async def trends(
    type: str = "daily",
    days: int = 7,
    weeks: int = 4,
    months: int = 12,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """获取提问趋势数据。

    - type: daily/weekly/monthly，默认 daily。
    - 当 type=daily 时使用 days 参数；
    - 当 type=weekly 时使用 weeks 参数；
    - 当 type=monthly 时使用 months 参数。
    """
    type_lower = (type or "daily").lower()
    if type_lower == "weekly":
        items = await trend_calculator.get_weekly_trend(db, weeks)
    elif type_lower == "monthly":
        items = await trend_calculator.get_monthly_trend(db, months)
    else:
        items = await trend_calculator.get_daily_trend(db, days)
    return {"type": type_lower, "total": len(items), "items": items}


@router.get("/intent-distribution", summary="意图分布")
async def intent_distribution(
    period: str = "week",
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """获取问题意图分布。"""
    items = await question_analyzer.get_intent_distribution(db, period)
    return {"period": period, "total": len(items), "items": items}


@router.get("/invalid-analysis", summary="无效问题分析")
async def invalid_analysis(
    period: str = "month",
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """获取无效问题分析报告。"""
    return await question_analyzer.get_invalid_analysis(db, period)


@router.post("/refresh", summary="手动刷新统计")
async def refresh(
    _: User = Depends(get_admin_user),
) -> dict:
    """手动刷新统计数据（占位接口，当前统计为实时查询无需刷新）。

    需要管理员权限。
    """
    return {"message": "统计为实时查询，无需手动刷新", "status": "ok"}
