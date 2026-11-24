"""文本清洗器。

提供去空行、去重、标准化、长度过滤等文本清洗能力。
"""
import re
from difflib import SequenceMatcher
from typing import List

from loguru import logger

# 连续空白（不含换行）正则
_MULTI_SPACES_RE = re.compile(r"[^\S\n]+")
# 连续换行正则
_MULTI_NEWLINES_RE = re.compile(r"\n{3,}")


class TextCleaner:
    """文本清洗器。

    所有方法均为纯函数式操作，可独立调用，也可通过 :meth:`clean` 一站式清洗。
    """

    def __init__(self) -> None:
        logger.debug("TextCleaner 已初始化")

    @staticmethod
    def remove_empty_lines(text: str) -> str:
        """移除空行与仅含空白的行。

        Args:
            text: 原始文本。

        Returns:
            去除空行后的文本。
        """
        if not text:
            return ""
        lines = [line.strip() for line in text.splitlines()]
        # 过滤掉空行
        kept = [line for line in lines if line]
        return "\n".join(kept)

    @staticmethod
    def normalize(text: str) -> str:
        """标准化空格与换行。

        - 将 Windows/旧 Mac 换行统一为 ``\\n``；
        - 连续空格压缩为单个空格；
        - 三个及以上换行压缩为两个。

        Args:
            text: 原始文本。

        Returns:
            标准化后的文本。
        """
        if not text:
            return ""
        # 统一换行符
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # 压缩行内连续空白（不含换行）
        text = _MULTI_SPACES_RE.sub(" ", text)
        # 去除行首行尾空格
        text = "\n".join(line.strip() for line in text.split("\n"))
        # 压缩连续空行
        text = _MULTI_NEWLINES_RE.sub("\n\n", text)
        return text.strip()

    @staticmethod
    def filter_by_length(
        texts: List[str], min_len: int = 10, max_len: int = 5000
    ) -> List[str]:
        """按长度过滤文本片段。

        Args:
            texts: 文本列表。
            min_len: 最小字符数（含），默认 10。
            max_len: 最大字符数（含），默认 5000。

        Returns:
            满足长度要求的文本列表。
        """
        if not texts:
            return []
        kept = [
            t for t in texts if t and min_len <= len(t.strip()) <= max_len
        ]
        logger.debug(
            f"长度过滤: 输入 {len(texts)} 条，保留 {len(kept)} 条"
            f"（范围 {min_len}-{max_len}）"
        )
        return kept

    @staticmethod
    def remove_duplicates(
        texts: List[str], threshold: float = 0.95
    ) -> List[str]:
        """基于相似度去重。

        使用 :class:`difflib.SequenceMatcher` 计算相似度，
        当与已保留文本的相似度大于等于 ``threshold`` 时视为重复。

        Args:
            texts: 文本列表。
            threshold: 相似度阈值，默认 0.95。

        Returns:
            去重后的文本列表，保持原始顺序。
        """
        if not texts:
            return []
        if not 0.0 <= threshold <= 1.0:
            logger.warning(
                f"非法阈值 {threshold}，已修正为 0.95"
            )
            threshold = 0.95

        kept: List[str] = []
        for candidate in texts:
            if not candidate:
                continue
            is_dup = False
            for existing in kept:
                ratio = SequenceMatcher(None, candidate, existing).ratio()
                if ratio >= threshold:
                    is_dup = True
                    break
            if not is_dup:
                kept.append(candidate)
        logger.debug(
            f"去重: 输入 {len(texts)} 条，保留 {len(kept)} 条（阈值 {threshold}）"
        )
        return kept

    def clean(self, text: str) -> str:
        """一站式清洗。

        依次执行：标准化 → 去空行。

        Args:
            text: 原始文本。

        Returns:
            清洗后的文本。
        """
        if not text:
            return ""
        text = self.normalize(text)
        text = self.remove_empty_lines(text)
        return text
