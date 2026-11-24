"""指标聚合服务。

基于 RetrievalMetrics / AnswerMetrics / LatencyMetrics / UserFeedback 表，
提供检索质量、回答质量、性能延迟与业务反馈的聚合统计能力，
为指标监控仪表盘与运营分析提供数据支撑。
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.metrics.latency_metrics import latency_metrics
from app.models.metrics import (
    AnswerMetrics,
    LatencyMetrics,
    RetrievalMetrics,
    UserFeedback,
)


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


def _normalize_period(period: str) -> str:
    """规范化周期标识为小写，默认 week。"""
    return (period or "week").lower()


def _period_minutes(period: str) -> Optional[int]:
    """根据周期标识计算总分钟数。

    Returns:
        总分钟数；all 返回 None（需基于实际数据跨度计算）。
    """
    days = _PERIOD_DAYS.get(_normalize_period(period), 7)
    if days is None:
        return None
    return days * 24 * 60


def _avg(values: List[float]) -> float:
    """计算均值，空列表返回 0.0。"""
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


# 命中标记表达式：hit_count 非空且大于 0 视为命中
_RETRIEVAL_HIT_EXPR = case(
    (
        and_(
            RetrievalMetrics.hit_count.isnot(None),
            RetrievalMetrics.hit_count > 0,
        ),
        1,
    ),
    else_=0,
)


class MetricsService:
    """指标聚合服务。"""

    # ------------------------------------------------------------------ #
    # 公共接口
    # ------------------------------------------------------------------ #
    async def get_overview(
        self,
        db: AsyncSession,
        period: str = "week",
        knowledge_base_id: int | None = None,
    ) -> dict:
        """返回四维度指标汇总概览（检索/回答/性能/业务）。

        Args:
            db: 异步数据库会话。
            period: 统计周期，day/week/month/all 之一。
            knowledge_base_id: 知识库 ID，可选筛选。
                TODO: 当前 QuestionLog 表无 knowledge_base_id 字段，
                指标表无法直接关联知识库，该参数暂未实际过滤，仅做透传保留。

        Returns:
            包含 retrieval / answer / latency / business 四部分的概览字典。
        """
        period = _normalize_period(period)

        retrieval = await self.get_retrieval_metrics(db, period, knowledge_base_id)
        answer = await self.get_answer_metrics(db, period, knowledge_base_id)
        latency = await self.get_latency_metrics(db, period, knowledge_base_id)
        feedback = answer.get("feedback", {})

        logger.info(
            f"指标总览查询完成: period={period}, knowledge_base_id={knowledge_base_id}"
        )
        return {
            "period": period,
            "retrieval": {
                "total_queries": retrieval["total_queries"],
                "hit_rate": retrieval["hit_rate"],
                "avg_retrieved_count": retrieval["avg_retrieved_count"],
            },
            "answer": {
                "total_answers": answer["answer"]["total_answers"],
                "citation_rate": answer["answer"]["citation_rate"],
                "downvote_rate": feedback.get("downvote_rate", 0.0),
                "hallucination_rate": answer["answer"]["hallucination_rate"],
            },
            "latency": {
                "total_requests": latency["total_requests"],
                "avg_ttft_ms": latency["avg_ttft_ms"],
                "p95_e2e_ms": latency["p95_e2e_ms"],
            },
            "business": {
                "total_feedback": feedback.get("total_feedback", 0),
                "upvote_count": feedback.get("upvote_count", 0),
                "downvote_count": feedback.get("downvote_count", 0),
            },
        }

    async def get_retrieval_metrics(
        self,
        db: AsyncSession,
        period: str = "week",
        knowledge_base_id: int | None = None,
    ) -> dict:
        """返回检索质量指标详情（命中率/MRR/召回数/耗时）。

        Args:
            db: 异步数据库会话。
            period: 统计周期，day/week/month/all 之一。
            knowledge_base_id: 知识库 ID，可选筛选（TODO: 暂未实现过滤）。

        Returns:
            检索质量指标字典，含 total_queries / hit_rate / mrr /
            avg_retrieved_count / avg_latency_ms / p95_latency_ms / trends。
        """
        period = _normalize_period(period)
        start = _get_period_start(period)
        # TODO: QuestionLog 无 knowledge_base_id 字段，暂不按知识库过滤。

        # 汇总统计
        stmt = select(
            func.count(RetrievalMetrics.id).label("total"),
            func.sum(_RETRIEVAL_HIT_EXPR).label("hits"),
            func.avg(RetrievalMetrics.retrieved_count).label("avg_retrieved"),
            func.avg(RetrievalMetrics.latency_ms).label("avg_latency"),
        )
        if start is not None:
            stmt = stmt.where(RetrievalMetrics.created_at >= start)
        row = (await db.execute(stmt)).one()
        total = int(row[0] or 0)
        hits = int(row[1] or 0)
        avg_retrieved = float(row[2]) if row[2] is not None else 0.0
        avg_latency = float(row[3]) if row[3] is not None else 0.0
        hit_rate = round(hits / total, 4) if total > 0 else 0.0

        # MRR：仅对有 first_relevant_rank 的记录计算 1/rank 的均值
        mrr_stmt = select(RetrievalMetrics.first_relevant_rank).where(
            RetrievalMetrics.first_relevant_rank.isnot(None),
            RetrievalMetrics.first_relevant_rank > 0,
        )
        if start is not None:
            mrr_stmt = mrr_stmt.where(RetrievalMetrics.created_at >= start)
        ranks = [r[0] for r in (await db.execute(mrr_stmt)).all() if r[0]]
        mrr = (
            round(sum(1.0 / r for r in ranks) / len(ranks), 4) if ranks else 0.0
        )

        # P95 检索耗时
        lat_stmt = select(RetrievalMetrics.latency_ms)
        if start is not None:
            lat_stmt = lat_stmt.where(RetrievalMetrics.created_at >= start)
        lat_values = [
            r[0] for r in (await db.execute(lat_stmt)).all() if r[0] is not None
        ]
        p95_latency = (
            round(latency_metrics.percentile(lat_values, 95), 2)
            if lat_values
            else 0.0
        )

        # 每日趋势
        trend_stmt = (
            select(
                func.date(RetrievalMetrics.created_at).label("day"),
                func.count(RetrievalMetrics.id).label("count"),
                func.sum(_RETRIEVAL_HIT_EXPR).label("hits"),
            )
            .group_by(func.date(RetrievalMetrics.created_at))
            .order_by(func.date(RetrievalMetrics.created_at).asc())
        )
        if start is not None:
            trend_stmt = trend_stmt.where(RetrievalMetrics.created_at >= start)
        trend_rows = (await db.execute(trend_stmt)).all()
        count_map: Dict[str, Dict[str, Any]] = {
            str(r[0]): {"count": int(r[1] or 0), "hits": int(r[2] or 0)}
            for r in trend_rows
        }
        trends = self._fill_daily_series(
            count_map, start, datetime.now(), default={"count": 0, "hits": 0}
        )

        logger.info(
            f"检索指标查询完成: period={period}, total={total}, hit_rate={hit_rate}"
        )
        return {
            "period": period,
            "total_queries": total,
            "hit_rate": hit_rate,
            "mrr": mrr,
            "avg_retrieved_count": round(avg_retrieved, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "p95_latency_ms": p95_latency,
            "trends": trends,
        }

    async def get_answer_metrics(
        self,
        db: AsyncSession,
        period: str = "week",
        knowledge_base_id: int | None = None,
    ) -> dict:
        """返回回答质量指标详情（引用率/点踩率/幻觉率）。

        Args:
            db: 异步数据库会话。
            period: 统计周期，day/week/month/all 之一。
            knowledge_base_id: 知识库 ID，可选筛选（TODO: 暂未实现过滤）。

        Returns:
            包含 answer 与 feedback 两部分的字典。
        """
        period = _normalize_period(period)
        start = _get_period_start(period)
        # TODO: QuestionLog 无 knowledge_base_id 字段，暂不按知识库过滤。
        # user_feedback 表为消息级别反馈，无需按知识库过滤。

        citation_hit_expr = case(
            (AnswerMetrics.citation_count > 0, 1),
            else_=0,
        )
        hall_expr = case(
            (AnswerMetrics.hallucination_flag.is_(True), 1),
            else_=0,
        )
        rej_expr = case(
            (AnswerMetrics.rejection_flag.is_(True), 1),
            else_=0,
        )

        stmt = select(
            func.count(AnswerMetrics.id).label("total"),
            func.sum(citation_hit_expr).label("cited"),
            func.avg(AnswerMetrics.citation_count).label("avg_citation"),
            func.sum(hall_expr).label("hall"),
            func.sum(rej_expr).label("rej"),
            func.avg(AnswerMetrics.retry_count).label("avg_retry"),
            func.avg(AnswerMetrics.answer_length).label("avg_len"),
        )
        if start is not None:
            stmt = stmt.where(AnswerMetrics.created_at >= start)
        row = (await db.execute(stmt)).one()
        total = int(row[0] or 0)
        cited = int(row[1] or 0)
        avg_citation = float(row[2]) if row[2] is not None else 0.0
        hall = int(row[3] or 0)
        rej = int(row[4] or 0)
        avg_retry = float(row[5]) if row[5] is not None else 0.0
        avg_len = float(row[6]) if row[6] is not None else 0.0

        citation_rate = round(cited / total, 4) if total > 0 else 0.0
        hallucination_rate = round(hall / total, 4) if total > 0 else 0.0
        rejection_rate = round(rej / total, 4) if total > 0 else 0.0

        # 用户反馈统计
        upvote_expr = case(
            (UserFeedback.feedback_type == "upvote", 1),
            else_=0,
        )
        downvote_expr = case(
            (UserFeedback.feedback_type == "downvote", 1),
            else_=0,
        )
        fb_stmt = select(
            func.count(UserFeedback.id).label("total"),
            func.sum(upvote_expr).label("upvotes"),
            func.sum(downvote_expr).label("downvotes"),
            func.avg(UserFeedback.rating).label("avg_rating"),
        )
        if start is not None:
            fb_stmt = fb_stmt.where(UserFeedback.created_at >= start)
        fb_row = (await db.execute(fb_stmt)).one()
        total_feedback = int(fb_row[0] or 0)
        upvote_count = int(fb_row[1] or 0)
        downvote_count = int(fb_row[2] or 0)
        avg_rating = float(fb_row[3]) if fb_row[3] is not None else 0.0
        downvote_rate = (
            round(downvote_count / total_feedback, 4)
            if total_feedback > 0
            else 0.0
        )

        logger.info(
            f"回答指标查询完成: period={period}, total={total}, "
            f"feedback={total_feedback}, downvote_rate={downvote_rate}"
        )
        return {
            "period": period,
            "answer": {
                "total_answers": total,
                "citation_rate": citation_rate,
                "avg_citation_count": round(avg_citation, 2),
                "hallucination_rate": hallucination_rate,
                "rejection_rate": rejection_rate,
                "avg_retry_count": round(avg_retry, 2),
                "avg_answer_length": round(avg_len, 2),
            },
            "feedback": {
                "total_feedback": total_feedback,
                "upvote_count": upvote_count,
                "downvote_count": downvote_count,
                "downvote_rate": downvote_rate,
                "avg_rating": round(avg_rating, 2),
            },
        }

    async def get_latency_metrics(
        self,
        db: AsyncSession,
        period: str = "week",
        knowledge_base_id: int | None = None,
    ) -> dict:
        """返回性能延迟指标详情（TTFT/P95/QPM）。

        Args:
            db: 异步数据库会话。
            period: 统计周期，day/week/month/all 之一。
            knowledge_base_id: 知识库 ID，可选筛选（TODO: 暂未实现过滤）。

        Returns:
            性能延迟指标字典，含 TTFT / 端到端延迟的均值与分位、
            检索/生成平均耗时与 QPM。
        """
        period = _normalize_period(period)
        start = _get_period_start(period)
        # TODO: QuestionLog 无 knowledge_base_id 字段，暂不按知识库过滤。

        # 拉取所需字段，均值与分位均在 Python 端计算以保证一致性
        stmt = select(
            LatencyMetrics.ttft_ms,
            LatencyMetrics.e2e_latency_ms,
            LatencyMetrics.retrieval_latency_ms,
            LatencyMetrics.generation_latency_ms,
            LatencyMetrics.created_at,
        )
        if start is not None:
            stmt = stmt.where(LatencyMetrics.created_at >= start)
        rows = (await db.execute(stmt)).all()

        total_requests = len(rows)
        ttft_values = [r[0] for r in rows if r[0] is not None]
        e2e_values = [r[1] for r in rows if r[1] is not None]
        retrieval_values = [r[2] for r in rows if r[2] is not None]
        generation_values = [r[3] for r in rows if r[3] is not None]
        created_list = [r[4] for r in rows if r[4] is not None]

        # QPM：每分钟请求数
        minutes = _period_minutes(period)
        if minutes is None:
            # all 周期：基于实际数据跨度计算
            if len(created_list) >= 2:
                span = (
                    max(created_list) - min(created_list)
                ).total_seconds() / 60.0
                minutes = max(int(span), 1)
            elif len(created_list) == 1:
                minutes = 1
            else:
                minutes = 0
        qpm = round(total_requests / minutes, 2) if minutes > 0 else 0.0

        logger.info(
            f"延迟指标查询完成: period={period}, total={total_requests}, qpm={qpm}"
        )
        return {
            "period": period,
            "total_requests": total_requests,
            "avg_ttft_ms": _avg(ttft_values),
            "p50_ttft_ms": round(latency_metrics.percentile(ttft_values, 50), 2),
            "p95_ttft_ms": round(latency_metrics.percentile(ttft_values, 95), 2),
            "avg_e2e_ms": _avg(e2e_values),
            "p50_e2e_ms": round(latency_metrics.percentile(e2e_values, 50), 2),
            "p95_e2e_ms": round(latency_metrics.percentile(e2e_values, 95), 2),
            "p99_e2e_ms": round(latency_metrics.percentile(e2e_values, 99), 2),
            "avg_retrieval_latency_ms": _avg(retrieval_values),
            "avg_generation_latency_ms": _avg(generation_values),
            "qpm": qpm,
        }

    async def get_metrics_trends(
        self,
        db: AsyncSession,
        period: str = "week",
        metric_type: str = "latency",
        knowledge_base_id: int | None = None,
    ) -> dict:
        """返回指定指标类型的时序数据。

        Args:
            db: 异步数据库会话。
            period: 统计周期，day/week/month/all 之一。
            metric_type: 指标类型，latency / retrieval / answer 之一。
            knowledge_base_id: 知识库 ID，可选筛选（TODO: 暂未实现过滤）。

        Returns:
            ``{"metric_type": str, "period": str, "items": [...]}``，
            items 按 date(created_at) 分组的每日聚合值。
        """
        period = _normalize_period(period)
        metric_type = (metric_type or "latency").lower()
        start = _get_period_start(period)
        # TODO: QuestionLog 无 knowledge_base_id 字段，暂不按知识库过滤。

        if metric_type == "retrieval":
            items = await self._retrieval_daily(db, start)
        elif metric_type == "answer":
            items = await self._answer_daily(db, start)
        else:  # latency（默认）
            items = await self._latency_daily(db, start)

        logger.info(
            f"指标趋势查询完成: period={period}, metric_type={metric_type}, "
            f"items={len(items)}"
        )
        return {
            "metric_type": metric_type,
            "period": period,
            "items": items,
        }

    # ------------------------------------------------------------------ #
    # 内部方法：每日聚合
    # ------------------------------------------------------------------ #
    async def _latency_daily(
        self, db: AsyncSession, start: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """每日延迟聚合：avg_e2e_ms / p95_e2e_ms / count。"""
        stmt = select(
            func.date(LatencyMetrics.created_at).label("day"),
            LatencyMetrics.e2e_latency_ms,
        )
        if start is not None:
            stmt = stmt.where(LatencyMetrics.created_at >= start)
        result = await db.execute(stmt)

        day_map: Dict[str, List[float]] = {}
        for row in result.all():
            if row[1] is None:
                continue
            day_map.setdefault(str(row[0]), []).append(float(row[1]))

        count_map: Dict[str, Dict[str, Any]] = {
            day: {
                "avg_e2e_ms": _avg(values),
                "p95_e2e_ms": round(
                    latency_metrics.percentile(values, 95), 2
                ),
                "count": len(values),
            }
            for day, values in day_map.items()
        }
        return self._fill_daily_series(
            count_map,
            start,
            datetime.now(),
            default={"avg_e2e_ms": 0.0, "p95_e2e_ms": 0.0, "count": 0},
        )

    async def _retrieval_daily(
        self, db: AsyncSession, start: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """每日检索聚合：total / hits / hit_rate。"""
        stmt = (
            select(
                func.date(RetrievalMetrics.created_at).label("day"),
                func.count(RetrievalMetrics.id).label("total"),
                func.sum(_RETRIEVAL_HIT_EXPR).label("hits"),
            )
            .group_by(func.date(RetrievalMetrics.created_at))
            .order_by(func.date(RetrievalMetrics.created_at).asc())
        )
        if start is not None:
            stmt = stmt.where(RetrievalMetrics.created_at >= start)
        result = await db.execute(stmt)

        count_map: Dict[str, Dict[str, Any]] = {}
        for row in result.all():
            total = int(row[1] or 0)
            hits = int(row[2] or 0)
            hit_rate = round(hits / total, 4) if total > 0 else 0.0
            count_map[str(row[0])] = {
                "total": total,
                "hits": hits,
                "hit_rate": hit_rate,
            }
        return self._fill_daily_series(
            count_map,
            start,
            datetime.now(),
            default={"total": 0, "hits": 0, "hit_rate": 0.0},
        )

    async def _answer_daily(
        self, db: AsyncSession, start: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """每日回答聚合：total / citations / downvotes。"""
        # 回答数与引用数（来自 AnswerMetrics）
        ans_stmt = (
            select(
                func.date(AnswerMetrics.created_at).label("day"),
                func.count(AnswerMetrics.id).label("total"),
                func.sum(AnswerMetrics.citation_count).label("citations"),
            )
            .group_by(func.date(AnswerMetrics.created_at))
        )
        if start is not None:
            ans_stmt = ans_stmt.where(AnswerMetrics.created_at >= start)
        ans_result = await db.execute(ans_stmt)

        count_map: Dict[str, Dict[str, Any]] = {}
        for row in ans_result.all():
            count_map[str(row[0])] = {
                "total": int(row[1] or 0),
                "citations": int(row[2] or 0),
                "downvotes": 0,
            }

        # 点踩数（来自 UserFeedback）
        dv_stmt = (
            select(
                func.date(UserFeedback.created_at).label("day"),
                func.count(UserFeedback.id).label("downvotes"),
            )
            .where(UserFeedback.feedback_type == "downvote")
            .group_by(func.date(UserFeedback.created_at))
        )
        if start is not None:
            dv_stmt = dv_stmt.where(UserFeedback.created_at >= start)
        dv_result = await db.execute(dv_stmt)
        for row in dv_result.all():
            day_str = str(row[0])
            if day_str not in count_map:
                count_map[day_str] = {
                    "total": 0,
                    "citations": 0,
                    "downvotes": 0,
                }
            count_map[day_str]["downvotes"] = int(row[1] or 0)

        return self._fill_daily_series(
            count_map,
            start,
            datetime.now(),
            default={"total": 0, "citations": 0, "downvotes": 0},
        )

    # ------------------------------------------------------------------ #
    # 内部工具
    # ------------------------------------------------------------------ #
    @staticmethod
    def _fill_daily_series(
        count_map: Dict[str, Dict[str, Any]],
        start: Optional[datetime],
        end: datetime,
        default: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """填充缺失日期，返回按日期升序的时序序列。

        Args:
            count_map: 日期字符串到指标字典的映射。
            start: 起始时间；为 None（all 周期）时仅返回数据中存在的日期。
            end: 截止时间（含）。
            default: 缺失日期的默认指标字典。

        Returns:
            时序列表，每个元素为 ``{"date": str, **metrics}``。
        """
        if start is None:
            items: List[Dict[str, Any]] = []
            for day_str in sorted(count_map.keys()):
                data = {"date": day_str}
                data.update(default)
                data.update(count_map[day_str])
                items.append(data)
            return items

        start_day = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end_day = end.replace(hour=0, minute=0, second=0, microsecond=0)
        items = []
        cur = start_day
        while cur <= end_day:
            day_str = cur.strftime("%Y-%m-%d")
            data = {"date": day_str}
            data.update(default)
            data.update(count_map.get(day_str, {}))
            items.append(data)
            cur += timedelta(days=1)
        return items


# 模块级单例
metrics_service = MetricsService()
