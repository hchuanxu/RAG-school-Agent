"""趋势计算器。

基于 QuestionLog 表提供日、周、月维度的提问趋势统计，以及自定义周期的环比分析。
"""
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.faq import QuestionLog


def _start_of_day(dt: datetime) -> datetime:
    """获取 dt 当天的 00:00:00。"""
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _start_of_week(dt: datetime) -> datetime:
    """获取 dt 所在周的周一 00:00:00（按 ISO 周）。"""
    start = _start_of_day(dt)
    # weekday(): 周一为 0，周日为 6
    return start - timedelta(days=start.weekday())


def _start_of_month(dt: datetime) -> datetime:
    """获取 dt 所在月份的 1 号 00:00:00。"""
    return _start_of_day(dt).replace(day=1)


class TrendCalculator:
    """趋势计算器。"""

    async def get_daily_trend(
        self, db: AsyncSession, days: int = 7
    ) -> List[Dict[str, Any]]:
        """获取日趋势。

        Args:
            db: 异步数据库会话。
            days: 统计天数，默认 7。

        Returns:
            日趋势列表，元素为 ``{date, count}``，按日期升序。
        """
        days = max(1, min(int(days or 7), 365))
        today = _start_of_day(datetime.now())
        start = today - timedelta(days=days - 1)

        # 按日期分组聚合
        stmt = (
            select(
                func.date(QuestionLog.asked_at).label("day"),
                func.count(QuestionLog.id).label("count"),
            )
            .where(QuestionLog.asked_at >= start)
            .group_by(func.date(QuestionLog.asked_at))
            .order_by(func.date(QuestionLog.asked_at).asc())
        )
        result = await db.execute(stmt)
        rows = result.all()

        # 构建日期到计数的映射
        count_map: Dict[str, int] = {
            str(row[0]): int(row[1] or 0) for row in rows
        }

        # 填充缺失日期（计数为 0）
        trend: List[Dict[str, Any]] = []
        for i in range(days):
            current = start + timedelta(days=i)
            date_str = current.strftime("%Y-%m-%d")
            trend.append({"date": date_str, "count": count_map.get(date_str, 0)})

        logger.info(f"日趋势查询完成: days={days}, total={sum(t['count'] for t in trend)}")
        return trend

    async def get_weekly_trend(
        self, db: AsyncSession, weeks: int = 4
    ) -> List[Dict[str, Any]]:
        """获取周趋势。

        Args:
            db: 异步数据库会话。
            weeks: 统计周数，默认 4。

        Returns:
            周趋势列表，元素为 ``{week, count}``，按周升序。
        """
        weeks = max(1, min(int(weeks or 4), 52))
        now = datetime.now()
        current_week_start = _start_of_week(now)
        first_week_start = current_week_start - timedelta(weeks=weeks - 1)

        # 按周分组聚合：使用 asked_at 落在的周一日期作为分组键
        # SQLite 与通用 SQL 兼容：使用 julianday 计算偏移
        # 此处采用 Python 端聚合以兼容多数据库
        stmt = select(QuestionLog.asked_at).where(
            QuestionLog.asked_at >= first_week_start
        )
        result = await db.execute(stmt)
        all_dates = [row[0] for row in result.all() if row[0]]

        # 按周聚合
        week_counts: Dict[str, int] = {}
        for asked_at in all_dates:
            week_start = _start_of_week(asked_at)
            week_label = week_start.strftime("%Y-%m-%d")
            week_counts[week_label] = week_counts.get(week_label, 0) + 1

        # 填充缺失周
        trend: List[Dict[str, Any]] = []
        for i in range(weeks):
            week_start = first_week_start + timedelta(weeks=i)
            week_label = week_start.strftime("%Y-%m-%d")
            trend.append(
                {
                    "week": week_label,
                    "count": week_counts.get(week_label, 0),
                }
            )

        logger.info(
            f"周趋势查询完成: weeks={weeks}, total={sum(t['count'] for t in trend)}"
        )
        return trend

    async def get_monthly_trend(
        self, db: AsyncSession, months: int = 12
    ) -> List[Dict[str, Any]]:
        """获取月趋势。

        Args:
            db: 异步数据库会话。
            months: 统计月数，默认 12。

        Returns:
            月趋势列表，元素为 ``{month, count}``，按月升序。
        """
        months = max(1, min(int(months or 12), 60))
        now = datetime.now()
        current_month_start = _start_of_month(now)
        # 计算起始月：从当前月往前推 months-1 个月
        start_year = now.year
        start_month = now.month - (months - 1)
        while start_month <= 0:
            start_month += 12
            start_year -= 1
        first_month_start = datetime(start_year, start_month, 1)

        stmt = select(QuestionLog.asked_at).where(
            QuestionLog.asked_at >= first_month_start
        )
        result = await db.execute(stmt)
        all_dates = [row[0] for row in result.all() if row[0]]

        # 按月聚合
        month_counts: Dict[str, int] = {}
        for asked_at in all_dates:
            month_label = asked_at.strftime("%Y-%m")
            month_counts[month_label] = month_counts.get(month_label, 0) + 1

        # 填充缺失月
        trend: List[Dict[str, Any]] = []
        for i in range(months):
            # 计算第 i 个月
            year = start_year
            month = start_month + i
            while month > 12:
                month -= 12
                year += 1
            month_label = f"{year:04d}-{month:02d}"
            trend.append(
                {
                    "month": month_label,
                    "count": month_counts.get(month_label, 0),
                }
            )

        logger.info(
            f"月趋势查询完成: months={months}, total={sum(t['count'] for t in trend)}"
        )
        return trend

    async def compare_periods(
        self,
        db: AsyncSession,
        current_start: datetime,
        current_end: datetime,
        previous_start: datetime,
        previous_end: datetime,
    ) -> Dict[str, Any]:
        """环比分析：比较当前周期与上一周期的提问量。

        Args:
            db: 异步数据库会话。
            current_start: 当前周期起始时间。
            current_end: 当前周期结束时间。
            previous_start: 上一周期起始时间。
            previous_end: 上一周期结束时间。

        Returns:
            ``{current_count, previous_count, diff, growth_rate, change}``。
            change 为 "up" / "down" / "flat"。
        """
        current_count = await self._count_in_range(
            db, current_start, current_end
        )
        previous_count = await self._count_in_range(
            db, previous_start, previous_end
        )

        diff = current_count - previous_count
        if previous_count == 0:
            growth_rate = 100.0 if current_count > 0 else 0.0
        else:
            growth_rate = round(diff / previous_count * 100, 2)

        if diff > 0:
            change = "up"
        elif diff < 0:
            change = "down"
        else:
            change = "flat"

        logger.info(
            f"环比分析完成: current={current_count}({current_start}~{current_end}), "
            f"previous={previous_count}({previous_start}~{previous_end}), "
            f"change={change}, rate={growth_rate}%"
        )
        return {
            "current_count": current_count,
            "previous_count": previous_count,
            "diff": diff,
            "growth_rate": growth_rate,
            "change": change,
            "current_period": {
                "start": current_start.isoformat(),
                "end": current_end.isoformat(),
            },
            "previous_period": {
                "start": previous_start.isoformat(),
                "end": previous_end.isoformat(),
            },
        }

    # ------------------------------------------------------------------ #
    # 内部方法
    # ------------------------------------------------------------------ #
    async def _count_in_range(
        self,
        db: AsyncSession,
        start: datetime,
        end: datetime,
    ) -> int:
        """统计指定时间范围内的问题数（闭区间 [start, end]）。"""
        stmt = select(func.count(QuestionLog.id)).where(
            QuestionLog.asked_at >= start,
            QuestionLog.asked_at <= end,
        )
        result = await db.execute(stmt)
        return int(result.scalar_one() or 0)


# 模块级单例
trend_calculator = TrendCalculator()
