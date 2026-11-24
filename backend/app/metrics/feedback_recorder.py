"""用户反馈记录器。

基于 UserFeedback 表记录用户对回答的点赞/点踩、评分与文字反馈，
支持反馈覆盖更新与按消息维度的统计聚合。
"""
from typing import Optional

from loguru import logger
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.metrics import UserFeedback


class FeedbackRecorder:
    """用户反馈记录器。"""

    async def record_feedback(
        self,
        db: AsyncSession,
        user_id: int,
        message_id: int,
        feedback_type: str,
        rating: Optional[int] = None,
        text: Optional[str] = None,
    ) -> Optional[int]:
        """记录或更新用户反馈。

        若同一 (user_id, message_id) 已存在反馈记录，则覆盖更新
        feedback_type / rating / feedback_text；否则新建记录。

        Args:
            db: 异步数据库会话。
            user_id: 用户 ID。
            message_id: 消息 ID。
            feedback_type: 反馈类型，upvote / downvote。
            rating: 1-5 星评分，可选。
            text: 文字反馈，可选。

        Returns:
            反馈记录 ID；若开关关闭、参数非法或写入失败则返回 None。
        """
        if not getattr(settings, "METRICS_ENABLED", True):
            return None

        if feedback_type not in ("upvote", "downvote"):
            logger.warning(
                f"非法 feedback_type={feedback_type}, "
                f"user_id={user_id}, message_id={message_id}"
            )
            return None

        if rating is not None and not (1 <= rating <= 5):
            logger.warning(
                f"非法 rating={rating} 已置空, "
                f"user_id={user_id}, message_id={message_id}"
            )
            rating = None

        try:
            existing = await self.get_feedback(db, user_id, message_id)
            if existing is not None:
                existing.feedback_type = feedback_type
                existing.rating = rating
                existing.feedback_text = text
                feedback = existing
            else:
                feedback = UserFeedback(
                    user_id=user_id,
                    message_id=message_id,
                    feedback_type=feedback_type,
                    rating=rating,
                    feedback_text=text,
                )
                db.add(feedback)

            await db.commit()
            await db.refresh(feedback)
            logger.info(
                f"用户反馈已记录: id={feedback.id}, user_id={user_id}, "
                f"message_id={message_id}, type={feedback_type}, rating={rating}"
            )
            return feedback.id
        except Exception:
            logger.exception(
                f"记录用户反馈失败: user_id={user_id}, message_id={message_id}"
            )
            return None

    async def get_feedback(
        self, db: AsyncSession, user_id: int, message_id: int
    ) -> Optional[UserFeedback]:
        """查询指定用户对指定消息的反馈记录。

        Args:
            db: 异步数据库会话。
            user_id: 用户 ID。
            message_id: 消息 ID。

        Returns:
            UserFeedback 对象或 None；查询失败也返回 None。
        """
        try:
            stmt = select(UserFeedback).where(
                UserFeedback.user_id == user_id,
                UserFeedback.message_id == message_id,
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception:
            logger.exception(
                f"查询用户反馈失败: user_id={user_id}, message_id={message_id}"
            )
            return None

    async def get_feedback_stats(self, db: AsyncSession, message_id: int) -> dict:
        """统计指定消息的反馈情况。

        Args:
            db: 异步数据库会话。
            message_id: 消息 ID。

        Returns:
            ``{"upvote": int, "downvote": int, "avg_rating": float or None, "total": int}``。
            avg_rating 为有评分记录的平均分，无评分时为 None；
            查询失败返回 ``{"upvote": 0, "downvote": 0, "avg_rating": None, "total": 0}``。
        """
        try:
            stmt = (
                select(
                    func.count(UserFeedback.id),
                    func.coalesce(
                        func.sum(
                            case(
                                (
                                    UserFeedback.feedback_type == "upvote",
                                    1,
                                ),
                                else_=0,
                            )
                        ),
                        0,
                    ),
                    func.coalesce(
                        func.sum(
                            case(
                                (
                                    UserFeedback.feedback_type == "downvote",
                                    1,
                                ),
                                else_=0,
                            )
                        ),
                        0,
                    ),
                    func.avg(UserFeedback.rating),
                )
                .where(UserFeedback.message_id == message_id)
            )
            result = await db.execute(stmt)
            row = result.one()
            total = int(row[0] or 0)
            upvote = int(row[1] or 0)
            downvote = int(row[2] or 0)
            avg_rating = round(float(row[3]), 2) if row[3] is not None else None
            logger.info(
                f"消息反馈统计完成: message_id={message_id}, total={total}, "
                f"upvote={upvote}, downvote={downvote}, avg_rating={avg_rating}"
            )
            return {
                "upvote": upvote,
                "downvote": downvote,
                "avg_rating": avg_rating,
                "total": total,
            }
        except Exception:
            logger.exception(f"统计消息反馈失败: message_id={message_id}")
            return {"upvote": 0, "downvote": 0, "avg_rating": None, "total": 0}


# 模块级单例
feedback_recorder = FeedbackRecorder()
