"""检索质量指标采集器。

基于 RetrievalMetrics 表记录单次问答的召回数量、命中标注与检索耗时，
为检索效果评估与知识库优化提供数据支撑。
"""
from typing import List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.chat import ChatMessage
from app.models.metrics import RetrievalMetrics


class RecallMetrics:
    """检索质量指标采集器。"""

    async def record_retrieval(
        self,
        db: AsyncSession,
        question_log_id: Optional[int],
        retrieved_count: int,
        top_scores: List[float],
        latency_ms: int,
        session_id: Optional[int] = None,
    ) -> Optional[int]:
        """记录一条检索质量指标。

        Args:
            db: 异步数据库会话。
            question_log_id: 关联的问题日志 ID，可选。
            retrieved_count: 召回文档切片数。
            top_scores: Top-K 检索得分列表。
            latency_ms: 检索耗时毫秒。
            session_id: 关联的会话 ID，可选。

        Returns:
            新建记录的 id；若指标采集关闭或写入失败则返回 None。
        """
        if not getattr(settings, "METRICS_ENABLED", True):
            return None

        try:
            metrics = RetrievalMetrics(
                question_log_id=question_log_id,
                session_id=session_id,
                retrieved_count=retrieved_count,
                top_scores=top_scores,
                latency_ms=latency_ms,
            )
            db.add(metrics)
            await db.commit()
            await db.refresh(metrics)
            logger.info(
                f"检索指标记录成功: question_log_id={question_log_id}, "
                f"retrieved_count={retrieved_count}, latency_ms={latency_ms}"
            )
            return metrics.id
        except Exception:
            logger.exception(
                f"检索指标记录失败: question_log_id={question_log_id}"
            )
            return None

    async def update_hit_annotation(
        self,
        db: AsyncSession,
        question_log_id: int,
        hit_count: int,
        first_relevant_rank: Optional[int] = None,
    ) -> bool:
        """根据问题日志 ID 更新命中标注。

        Args:
            db: 异步数据库会话。
            question_log_id: 问题日志 ID。
            hit_count: 命中数量。
            first_relevant_rank: 首位命中排名，可选。

        Returns:
            更新成功返回 True，未找到记录或失败返回 False。
        """
        try:
            stmt = (
                select(RetrievalMetrics)
                .where(RetrievalMetrics.question_log_id == question_log_id)
                .order_by(RetrievalMetrics.id.desc())
                .limit(1)
            )
            result = await db.execute(stmt)
            metrics = result.scalar_one_or_none()
            if metrics is None:
                logger.warning(
                    f"更新命中标注未找到记录: question_log_id={question_log_id}"
                )
                return False
            metrics.hit_count = hit_count
            if first_relevant_rank is not None:
                metrics.first_relevant_rank = first_relevant_rank
            await db.commit()
            logger.info(
                f"命中标注更新成功: question_log_id={question_log_id}, "
                f"hit_count={hit_count}, first_relevant_rank={first_relevant_rank}"
            )
            return True
        except Exception:
            logger.exception(
                f"更新命中标注失败: question_log_id={question_log_id}"
            )
            return False

    async def update_hit_by_message(
        self, db: AsyncSession, message_id: int, hit: bool
    ) -> bool:
        """通过消息 ID 反向标注检索命中情况。

        用于用户点踩/点赞时反向更新对应检索记录：
        - 点赞（hit=True）：视为命中，hit_count=1，first_relevant_rank=1。
        - 点踩（hit=False）：视为未命中，hit_count=0。

        通过 message_id 查 ChatMessage 获取 session_id，
        再更新该会话最近一条检索记录。

        Args:
            db: 异步数据库会话。
            message_id: 聊天消息 ID。
            hit: 是否命中。

        Returns:
            更新成功返回 True，未找到记录或失败返回 False。
        """
        try:
            # 通过 message_id 查 ChatMessage 拿到 session_id
            msg_stmt = select(ChatMessage.session_id).where(
                ChatMessage.id == message_id
            )
            msg_result = await db.execute(msg_stmt)
            session_id = msg_result.scalar_one_or_none()
            if session_id is None:
                logger.warning(
                    f"反向标注命中未找到消息: message_id={message_id}"
                )
                return False

            # 查该会话最近的 RetrievalMetrics 记录
            stmt = (
                select(RetrievalMetrics)
                .where(RetrievalMetrics.session_id == session_id)
                .order_by(RetrievalMetrics.id.desc())
                .limit(1)
            )
            result = await db.execute(stmt)
            metrics = result.scalar_one_or_none()
            if metrics is None:
                logger.warning(
                    f"反向标注命中未找到检索记录: message_id={message_id}, "
                    f"session_id={session_id}"
                )
                return False

            if hit:
                metrics.hit_count = 1
                metrics.first_relevant_rank = 1
            else:
                metrics.hit_count = 0
            await db.commit()
            logger.info(
                f"反向标注命中成功: message_id={message_id}, "
                f"session_id={session_id}, hit={hit}"
            )
            return True
        except Exception:
            logger.exception(
                f"反向标注命中失败: message_id={message_id}"
            )
            return False


# 模块级单例
recall_metrics = RecallMetrics()
