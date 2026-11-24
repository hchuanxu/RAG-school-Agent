"""性能延迟指标采集器。

基于 LatencyMetrics 表记录问答各阶段（首字、检索、生成、端到端）耗时，
为性能分析与监控提供数据支撑。
"""
from typing import List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.metrics import LatencyMetrics


class LatencyMetricsCollector:
    """性能延迟指标采集器。"""

    async def record_ttft(
        self,
        db: AsyncSession,
        session_id: Optional[int],
        message_id: Optional[int],
        ttft_ms: int,
    ) -> Optional[int]:
        """记录首字延迟（TTFT）。

        若同一 session_id + message_id 已存在记录则更新，否则新建。

        Args:
            db: 异步数据库会话。
            session_id: 会话 ID，可为 None。
            message_id: 消息 ID，可为 None。
            ttft_ms: 首字延迟毫秒数。

        Returns:
            记录 ID；指标开关关闭或写入失败时返回 None。
        """
        if not getattr(settings, "METRICS_ENABLED", True):
            return None

        try:
            stmt = select(LatencyMetrics).where(
                LatencyMetrics.session_id == session_id,
                LatencyMetrics.message_id == message_id,
            )
            result = await db.execute(stmt)
            record = result.scalar_one_or_none()

            if record is None:
                record = LatencyMetrics(
                    session_id=session_id,
                    message_id=message_id,
                    ttft_ms=ttft_ms,
                )
                db.add(record)
            else:
                record.ttft_ms = ttft_ms

            await db.commit()
            await db.refresh(record)
            return record.id
        except Exception:
            logger.exception(
                f"记录 TTFT 失败: session_id={session_id}, "
                f"message_id={message_id}, ttft_ms={ttft_ms}"
            )
            return None

    async def record_e2e_latency(
        self,
        db: AsyncSession,
        session_id: Optional[int],
        message_id: Optional[int],
        e2e_ms: int,
        retrieval_ms: Optional[int] = None,
        generation_ms: Optional[int] = None,
    ) -> Optional[int]:
        """记录端到端延迟及可选的检索/生成耗时。

        若同一 session_id + message_id 已存在记录则更新（仅当 retrieval_ms /
        generation_ms 非 None 时才覆盖对应字段），否则新建。

        Args:
            db: 异步数据库会话。
            session_id: 会话 ID，可为 None。
            message_id: 消息 ID，可为 None。
            e2e_ms: 端到端延迟毫秒数。
            retrieval_ms: 检索耗时毫秒数，可为 None。
            generation_ms: 生成耗时毫秒数，可为 None。

        Returns:
            记录 ID；指标开关关闭或写入失败时返回 None。
        """
        if not getattr(settings, "METRICS_ENABLED", True):
            return None

        try:
            stmt = select(LatencyMetrics).where(
                LatencyMetrics.session_id == session_id,
                LatencyMetrics.message_id == message_id,
            )
            result = await db.execute(stmt)
            record = result.scalar_one_or_none()

            if record is None:
                record = LatencyMetrics(
                    session_id=session_id,
                    message_id=message_id,
                    e2e_latency_ms=e2e_ms,
                    retrieval_latency_ms=retrieval_ms,
                    generation_latency_ms=generation_ms,
                )
                db.add(record)
            else:
                record.e2e_latency_ms = e2e_ms
                if retrieval_ms is not None:
                    record.retrieval_latency_ms = retrieval_ms
                if generation_ms is not None:
                    record.generation_latency_ms = generation_ms

            await db.commit()
            await db.refresh(record)
            return record.id
        except Exception:
            logger.exception(
                f"记录端到端延迟失败: session_id={session_id}, "
                f"message_id={message_id}, e2e_ms={e2e_ms}"
            )
            return None

    def percentile(self, values: List[float], p: float) -> float:
        """计算分位数（线性插值法）。

        Args:
            values: 数值列表。
            p: 百分位，0-100，如 50/95/99。

        Returns:
            分位数值；空列表返回 0.0。
        """
        if not values:
            return 0.0

        sorted_values = sorted(values)
        n = len(sorted_values)
        idx = (p / 100.0) * (n - 1)
        lower = int(idx)
        upper = min(lower + 1, n - 1)
        if lower == upper:
            return float(sorted_values[lower])

        frac = idx - lower
        return float(
            sorted_values[lower]
            + (sorted_values[upper] - sorted_values[lower]) * frac
        )


# 模块级单例
latency_metrics = LatencyMetricsCollector()
