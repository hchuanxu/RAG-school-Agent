"""文档切片器。

提供按大小、按段落、递归切片三种策略，并支持返回带位置信息的切片结果。
"""
import re
from typing import Dict, List

from loguru import logger

# 句子结束符（中英文）正则
_SENTENCE_END_RE = re.compile(r"(?<=[。！？!?\.])\s*")


class DocumentSplitter:
    """文档切片器。

    Args:
        chunk_size: 每个切片的目标字符数，默认 500。
        chunk_overlap: 切片间重叠字符数，默认 50。
    """

    def __init__(
        self, chunk_size: int = 500, chunk_overlap: int = 50
    ) -> None:
        if chunk_size <= 0:
            raise ValueError(f"chunk_size 必须为正数，当前: {chunk_size}")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap 必须满足 0 <= overlap < chunk_size，"
                f"当前 overlap={chunk_overlap}, chunk_size={chunk_size}"
            )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.debug(
            f"DocumentSplitter 已初始化: chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}"
        )

    def split_by_size(self, text: str) -> List[str]:
        """按固定字符数切片。

        使用滑动窗口，步长为 ``chunk_size - chunk_overlap``。

        Args:
            text: 待切片文本。

        Returns:
            切片文本列表。
        """
        if not text:
            return []
        chunks: List[str] = []
        step = self.chunk_size - self.chunk_overlap
        start = 0
        total = len(text)
        while start < total:
            end = min(start + self.chunk_size, total)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= total:
                break
            start += step
        logger.debug(f"按大小切片完成，共 {len(chunks)} 块")
        return chunks

    def split_by_paragraph(self, text: str) -> List[str]:
        """按段落切片，超长段落进一步按大小切分。

        Args:
            text: 待切片文本。

        Returns:
            切片文本列表。
        """
        if not text:
            return []
        # 按两个及以上换行切分段落；兼容单个换行
        paragraphs = [p.strip() for p in re.split(r"\n{1,}", text) if p.strip()]
        chunks: List[str] = []
        for para in paragraphs:
            if len(para) <= self.chunk_size:
                chunks.append(para)
            else:
                # 超长段落降级为按大小切分
                chunks.extend(self.split_by_size(para))
        logger.debug(f"按段落切片完成，共 {len(chunks)} 块")
        return chunks

    def split_recursively(self, text: str) -> List[str]:
        """递归切片。

        优先按段落切分；段落过长则按句子切分；
        句子仍过长则按大小切分。最终合并相邻片段以接近 ``chunk_size``，
        并保留 ``chunk_overlap`` 的重叠。

        Args:
            text: 待切片文本。

        Returns:
            切片文本列表。
        """
        if not text:
            return []

        # 第一层：按段落
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

        # 将段落进一步切分为句子级单元
        units: List[str] = []
        for para in paragraphs:
            if len(para) <= self.chunk_size:
                units.append(para)
                continue
            # 段落过长，按句子切分
            sentences = [
                s.strip() for s in _SENTENCE_END_RE.split(para) if s.strip()
            ]
            for sent in sentences:
                if len(sent) <= self.chunk_size:
                    units.append(sent)
                else:
                    # 句子仍过长，按大小切分
                    units.extend(self.split_by_size(sent))

        # 合并单元到目标大小
        chunks: List[str] = []
        current = ""
        for unit in units:
            if not current:
                current = unit
                continue
            # 尝试合并
            if len(current) + 1 + len(unit) <= self.chunk_size:
                current = current + "\n" + unit
            else:
                chunks.append(current)
                # 重叠：保留当前块末尾 overlap 字符作为下一块开头
                if self.chunk_overlap > 0:
                    tail = current[-self.chunk_overlap :]
                    current = (tail + "\n" + unit).strip()
                else:
                    current = unit
        if current:
            chunks.append(current)

        logger.debug(f"递归切片完成，共 {len(chunks)} 块")
        return chunks

    def split_document(
        self, text: str, strategy: str = "recursive"
    ) -> List[Dict]:
        """切片并返回带位置信息的结构化结果。

        Args:
            text: 待切片文本。
            strategy: 切片策略，可选 ``"size"`` / ``"paragraph"`` / ``"recursive"``，
                默认 ``"recursive"``。

        Returns:
            列表，元素为
            ``{"chunk_index": int, "content": str, "start_char": int, "end_char": int}``。

        Raises:
            ValueError: 当传入未知策略时。
        """
        strategy_map = {
            "size": self.split_by_size,
            "paragraph": self.split_by_paragraph,
            "recursive": self.split_recursively,
        }
        if strategy not in strategy_map:
            logger.error(f"未知切片策略: {strategy}")
            raise ValueError(
                f"未知切片策略: {strategy}，可选: {list(strategy_map.keys())}"
            )

        logger.info(f"开始切片，策略: {strategy}")
        chunks = strategy_map[strategy](text)

        # 计算每块在原文中的起止位置
        results: List[Dict] = []
        search_start = 0
        for index, chunk in enumerate(chunks):
            pos = text.find(chunk, search_start)
            if pos == -1:
                # 清洗后可能找不到精确匹配，退化为顺序估计
                start_char = search_start
                end_char = start_char + len(chunk)
            else:
                start_char = pos
                end_char = pos + len(chunk)
                search_start = end_char
            results.append(
                {
                    "chunk_index": index,
                    "content": chunk,
                    "start_char": start_char,
                    "end_char": end_char,
                }
            )
        logger.info(f"切片完成，策略={strategy}，共 {len(results)} 块")
        return results
