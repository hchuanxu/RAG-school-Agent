"""回答质量指标采集器。

基于 AnswerMetrics 表记录回答的引用数量、长度、幻觉与重试等质量信息，
为问答质量评估与运营分析提供数据支撑。
"""
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.metrics import AnswerMetrics


class AnswerMetricsCollector:
    """回答质量指标采集器。"""

    async def record_answer(
        self,
        db: AsyncSession,
        message_id: int,
        citation_count: int,
        answer_length: int,
        hallucination_flag: bool = False,
        rejection_flag: bool = False,
        retry_count: int = 0,
        session_id: Optional[int] = None,
    ) -> Optional[int]:
        """记录一条回答质量指标。

        Args:
            db: 异步数据库会话。
            message_id: 关联的聊天消息 ID。
            citation_count: 引用数量。
            answer_length: 回答字符数。
            hallucination_flag: 是否疑似幻觉。
            rejection_flag: 是否拒绝回答。
            retry_count: 重试次数。
            session_id: 关联的会话 ID，可选。

        Returns:
            新建记录的 id；若指标采集关闭或写入失败则返回 None。
        """
        if not getattr(settings, "METRICS_ENABLED", True):
            return None

        try:
            metrics = AnswerMetrics(
                message_id=message_id,
                session_id=session_id,
                citation_count=citation_count,
                answer_length=answer_length,
                hallucination_flag=hallucination_flag,
                rejection_flag=rejection_flag,
                retry_count=retry_count,
            )
            db.add(metrics)
            await db.commit()
            await db.refresh(metrics)
            logger.info(
                f"回答指标记录成功: message_id={message_id}, "
                f"citation_count={citation_count}, answer_length={answer_length}"
            )
            return metrics.id
        except Exception:
            logger.exception(
                f"回答指标记录失败: message_id={message_id}"
            )
            return None

    async def update_hallucination(
        self, db: AsyncSession, message_id: int, hallucination_flag: bool
    ) -> bool:
        """更新指定消息的幻觉标记。

        Args:
            db: 异步数据库会话。
            message_id: 聊天消息 ID。
            hallucination_flag: 是否疑似幻觉。

        Returns:
            更新成功返回 True，未找到记录或失败返回 False。
        """
        try:
            stmt = select(AnswerMetrics).where(
                AnswerMetrics.message_id == message_id
            )
            result = await db.execute(stmt)
            metrics = result.scalar_one_or_none()
            if metrics is None:
                logger.warning(
                    f"更新幻觉标记未找到记录: message_id={message_id}"
                )
                return False
            metrics.hallucination_flag = hallucination_flag
            await db.commit()
            logger.info(
                f"幻觉标记更新成功: message_id={message_id}, "
                f"hallucination_flag={hallucination_flag}"
            )
            return True
        except Exception:
            logger.exception(
                f"更新幻觉标记失败: message_id={message_id}"
            )
            return False

    async def update_retry_count(
        self, db: AsyncSession, message_id: int, retry_count: int
    ) -> bool:
        """更新指定消息的重试次数。

        Args:
            db: 异步数据库会话。
            message_id: 聊天消息 ID。
            retry_count: 重试次数。

        Returns:
            更新成功返回 True，未找到记录或失败返回 False。
        """
        try:
            stmt = select(AnswerMetrics).where(
                AnswerMetrics.message_id == message_id
            )
            result = await db.execute(stmt)
            metrics = result.scalar_one_or_none()
            if metrics is None:
                logger.warning(
                    f"更新重试次数未找到记录: message_id={message_id}"
                )
                return False
            metrics.retry_count = retry_count
            await db.commit()
            logger.info(
                f"重试次数更新成功: message_id={message_id}, "
                f"retry_count={retry_count}"
            )
            return True
        except Exception:
            logger.exception(
                f"更新重试次数失败: message_id={message_id}"
            )
            return False

    async def update_citation_accuracy(
        self, db: AsyncSession, message_id: int, accuracy: float
    ) -> bool:
        """更新指定消息的引用准确率。

        Args:
            db: 异步数据库会话。
            message_id: 聊天消息 ID。
            accuracy: 引用准确率，取值 0-1。

        Returns:
            更新成功返回 True，未找到记录或失败返回 False。
        """
        try:
            stmt = select(AnswerMetrics).where(
                AnswerMetrics.message_id == message_id
            )
            result = await db.execute(stmt)
            metrics = result.scalar_one_or_none()
            if metrics is None:
                logger.warning(
                    f"更新引用准确率未找到记录: message_id={message_id}"
                )
                return False
            metrics.citation_accuracy = accuracy
            await db.commit()
            logger.info(
                f"引用准确率更新成功: message_id={message_id}, "
                f"accuracy={accuracy}"
            )
            return True
        except Exception:
            logger.exception(
                f"更新引用准确率失败: message_id={message_id}"
            )
            return False


# 模块级单例
answer_metrics = AnswerMetricsCollector()
