"""问题记录器。

将用户提问记录到 QuestionLog 表，并提供文本清洗能力。
为热门问题统计与意图分析提供原始数据。
"""
import re
from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.faq import QuestionLog


# 多余空白字符正则
_MULTI_SPACES_RE = re.compile(r"\s+")
# 前后无意义字符
_TRIM_CHARS_RE = re.compile(r"^[\s?？\.。,，!！]+|[\s?？\.。,，!！]+$")


class QuestionRecorder:
    """问题记录器。"""

    # 问题最大长度（与数据库字段对齐）
    MAX_QUESTION_LENGTH = 512

    async def record(
        self,
        db: AsyncSession,
        question: str,
        intent: Optional[str] = None,
        is_valid: bool = True,
        user_id: Optional[int] = None,
        session_id: Optional[int] = None,
    ) -> Optional[QuestionLog]:
        """记录一条用户提问。

        Args:
            db: 异步数据库会话。
            question: 原始问题文本。
            intent: 意图分类结果，可选。
            is_valid: 是否为有效问题，默认 True。
            user_id: 提问用户 ID，可选。
            session_id: 会话 ID，可选。

        Returns:
            已记录的 QuestionLog 实例；问题为空则返回 None。
        """
        cleaned = await self.clean_question(question)
        if not cleaned:
            logger.debug("清洗后问题为空，跳过记录")
            return None

        if len(cleaned) > self.MAX_QUESTION_LENGTH:
            cleaned = cleaned[: self.MAX_QUESTION_LENGTH]

        log = QuestionLog(
            question=cleaned,
            intent=intent,
            is_valid=is_valid,
            user_id=user_id,
            session_id=session_id,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        logger.info(
            f"问题已记录: id={log.id}, intent={intent}, is_valid={is_valid}, "
            f"len={len(cleaned)}"
        )
        return log

    async def clean_question(self, question: str) -> str:
        """清洗问题文本。

        - 去除前后空白与无意义的标点；
        - 压缩内部多余空白为单个空格；
        - 统一全角空格。

        Args:
            question: 原始问题文本。

        Returns:
            清洗后的问题文本。
        """
        if not question:
            return ""
        text = question.strip()
        # 全角空格转半角
        text = text.replace("\u3000", " ")
        # 压缩多余空白
        text = _MULTI_SPACES_RE.sub(" ", text)
        # 去除前后无意义字符
        text = _TRIM_CHARS_RE.sub("", text)
        return text.strip()


# 模块级单例
question_recorder = QuestionRecorder()
