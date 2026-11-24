"""问题分析器。

基于 QuestionLog 表提供热门问题、意图分布与无效问题分析能力，
为 FAQ 自动生成与运营分析提供数据支撑。
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.faq import QuestionLog


# 周期到天数的映射
_PERIOD_DAYS = {
    "day": 1,
    "week": 7,
    "month": 30,
    "all": None,  # None 表示不限制时间
}


def _get_period_start(period: str) -> Optional[datetime]:
    """根据周期标识计算起始时间。

    Args:
        period: day/week/month/all 之一。

    Returns:
        起始时间；all 返回 None 表示不限时间。
    """
    period = (period or "week").lower()
    days = _PERIOD_DAYS.get(period, 7)
    if days is None:
        return None
    return datetime.now() - timedelta(days=days)


class QuestionAnalyzer:
    """问题分析器。"""

    async def get_hot_questions(
        self,
        db: AsyncSession,
        period: str = "week",
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """获取热门问题。

        Args:
            db: 异步数据库会话。
            period: 统计周期，day/week/month/all 之一。
            top_k: 返回前 N 条，默认 10。

        Returns:
            热门问题列表，元素为
            ``{question, count, percentage, intent, last_asked}``。
        """
        period = (period or "week").lower()
        top_k = max(1, min(int(top_k or 10), 100))
        start = _get_period_start(period)

        # 统计总问题数（用于百分比）
        total_stmt = select(func.count(QuestionLog.id))
        if start is not None:
            total_stmt = total_stmt.where(QuestionLog.asked_at >= start)
        total_result = await db.execute(total_stmt)
        total = int(total_result.scalar_one() or 0)

        # 按问题文本分组聚合
        stmt = (
            select(
                QuestionLog.question,
                func.count(QuestionLog.id).label("count"),
                func.max(QuestionLog.asked_at).label("last_asked"),
            )
            .group_by(QuestionLog.question)
            .order_by(func.count(QuestionLog.id).desc())
            .limit(top_k)
        )
        if start is not None:
            stmt = stmt.where(QuestionLog.asked_at >= start)
        result = await db.execute(stmt)
        rows = result.all()

        hot_questions: List[Dict[str, Any]] = []
        for row in rows:
            question_text = row[0]
            count = int(row[1] or 0)
            last_asked = row[2]
            # 查询该问题的主要意图
            intent = await self._get_primary_intent(db, question_text, start)
            percentage = round(count / total * 100, 2) if total > 0 else 0.0
            hot_questions.append(
                {
                    "question": question_text,
                    "count": count,
                    "percentage": percentage,
                    "intent": intent,
                    "last_asked": last_asked.isoformat() if last_asked else None,
                }
            )

        logger.info(
            f"热门问题查询完成: period={period}, total={total}, returned={len(hot_questions)}"
        )
        return hot_questions

    async def get_intent_distribution(
        self, db: AsyncSession, period: str = "week"
    ) -> List[Dict[str, Any]]:
        """获取意图分布。

        Args:
            db: 异步数据库会话。
            period: 统计周期。

        Returns:
            意图分布列表，元素为 ``{intent, count, percentage}``，按计数降序。
        """
        period = (period or "week").lower()
        start = _get_period_start(period)

        total_stmt = select(func.count(QuestionLog.id))
        if start is not None:
            total_stmt = total_stmt.where(QuestionLog.asked_at >= start)
        total_result = await db.execute(total_stmt)
        total = int(total_result.scalar_one() or 0)

        stmt = (
            select(
                QuestionLog.intent,
                func.count(QuestionLog.id).label("count"),
            )
            .group_by(QuestionLog.intent)
            .order_by(func.count(QuestionLog.id).desc())
        )
        if start is not None:
            stmt = stmt.where(QuestionLog.asked_at >= start)
        result = await db.execute(stmt)
        rows = result.all()

        distribution: List[Dict[str, Any]] = []
        for row in rows:
            intent = row[0] or "unknown"
            count = int(row[1] or 0)
            percentage = round(count / total * 100, 2) if total > 0 else 0.0
            distribution.append(
                {"intent": intent, "count": count, "percentage": percentage}
            )

        logger.info(
            f"意图分布查询完成: period={period}, total={total}, categories={len(distribution)}"
        )
        return distribution

    async def get_invalid_analysis(
        self, db: AsyncSession, period: str = "month"
    ) -> Dict[str, Any]:
        """获取无效问题分析。

        Args:
            db: 异步数据库会话。
            period: 统计周期，默认 month。

        Returns:
            ``{period, total, invalid_count, invalid_percentage, types, samples, suggestions}``。
            - types: 按意图分组的无效问题统计
            - samples: 无效问题样本列表
            - suggestions: 优化建议列表
        """
        period = (period or "month").lower()
        start = _get_period_start(period)

        # 总数与无效数
        total_stmt = select(func.count(QuestionLog.id))
        invalid_stmt = select(func.count(QuestionLog.id)).where(
            QuestionLog.is_valid.is_(False)
        )
        if start is not None:
            total_stmt = total_stmt.where(QuestionLog.asked_at >= start)
            invalid_stmt = invalid_stmt.where(QuestionLog.asked_at >= start)

        total = int((await db.execute(total_stmt)).scalar_one() or 0)
        invalid_count = int((await db.execute(invalid_stmt)).scalar_one() or 0)
        invalid_percentage = (
            round(invalid_count / total * 100, 2) if total > 0 else 0.0
        )

        # 按意图分组统计无效问题
        types_stmt = (
            select(
                QuestionLog.intent,
                func.count(QuestionLog.id).label("count"),
            )
            .where(QuestionLog.is_valid.is_(False))
            .group_by(QuestionLog.intent)
            .order_by(func.count(QuestionLog.id).desc())
        )
        if start is not None:
            types_stmt = types_stmt.where(QuestionLog.asked_at >= start)
        types_result = await db.execute(types_stmt)
        types_rows = types_result.all()

        types: List[Dict[str, Any]] = []
        for row in types_rows:
            intent = row[0] or "unknown"
            count = int(row[1] or 0)
            type_pct = (
                round(count / invalid_count * 100, 2) if invalid_count > 0 else 0.0
            )
            types.append(
                {"type": intent, "count": count, "percentage": type_pct}
            )

        # 查询无效问题样本（最多 20 条）
        samples_stmt = (
            select(QuestionLog.question, QuestionLog.intent, QuestionLog.asked_at)
            .where(QuestionLog.is_valid.is_(False))
            .order_by(QuestionLog.asked_at.desc())
            .limit(20)
        )
        if start is not None:
            samples_stmt = samples_stmt.where(QuestionLog.asked_at >= start)
        samples_result = await db.execute(samples_stmt)
        samples_rows = samples_result.all()

        samples: List[Dict[str, Any]] = []
        for row in samples_rows:
            samples.append(
                {
                    "question": row[0] or "",
                    "reason": f"意图分类：{row[1] or 'unknown'}" if row[1] else None,
                    "created_at": row[2].isoformat() if row[2] else None,
                }
            )

        # 生成建议列表
        suggestions = self._build_suggestions(
            invalid_count, invalid_percentage, types
        )

        logger.info(
            f"无效问题分析完成: period={period}, total={total}, invalid={invalid_count}"
        )
        return {
            "period": period,
            "total": total,
            "invalid_count": invalid_count,
            "invalid_percentage": invalid_percentage,
            "types": types,
            "samples": samples,
            "suggestions": suggestions,
        }

    # ------------------------------------------------------------------ #
    # 内部方法
    # ------------------------------------------------------------------ #
    async def _get_primary_intent(
        self,
        db: AsyncSession,
        question: str,
        start: Optional[datetime],
    ) -> Optional[str]:
        """获取指定问题文本出现次数最多的意图。"""
        stmt = (
            select(
                QuestionLog.intent,
                func.count(QuestionLog.id).label("count"),
            )
            .where(QuestionLog.question == question)
            .group_by(QuestionLog.intent)
            .order_by(func.count(QuestionLog.id).desc())
            .limit(1)
        )
        if start is not None:
            stmt = stmt.where(QuestionLog.asked_at >= start)
        result = await db.execute(stmt)
        row = result.first()
        return row[0] if row else None

    @staticmethod
    def _build_suggestions(
        invalid_count: int, invalid_percentage: float, types: List[Dict[str, Any]]
    ) -> List[str]:
        """根据无效问题分析结果生成运营建议列表。"""
        if invalid_count == 0:
            return ["暂无明显无效问题，问答质量良好。"]

        suggestions: List[str] = []
        if invalid_percentage >= 30:
            suggestions.append(
                f"无效问题占比偏高（{invalid_percentage}%），建议优化意图识别与知识库覆盖。"
            )
        elif invalid_percentage >= 10:
            suggestions.append(
                f"无效问题占比 {invalid_percentage}%，建议关注高频无效问题类型并补充相关知识。"
            )
        else:
            suggestions.append(
                f"无效问题占比 {invalid_percentage}%，整体问答质量较好。"
            )

        if types:
            top_type = types[0]
            suggestions.append(
                f"主要无效类型为「{top_type.get('type')}」，"
                f"共 {top_type.get('count')} 条，建议针对性优化。"
            )
        return suggestions


# 模块级单例
question_analyzer = QuestionAnalyzer()
