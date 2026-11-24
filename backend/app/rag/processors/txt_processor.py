"""TXT 文档解析器。

读取纯文本文件，自动检测 UTF-8/GBK 编码，支持全文与按行提取。
"""
from pathlib import Path
from typing import Dict, List

from loguru import logger

# 候选编码，按优先级尝试
_CANDIDATE_ENCODINGS = ("utf-8", "utf-8-sig", "gbk", "gb18030", "big5")


class TXTProcessor:
    """TXT 文档解析器。

    自动检测文件编码，提供全文与按行提取能力。
    """

    SUPPORTED_EXT = ".txt"

    def __init__(self) -> None:
        logger.debug("TXTProcessor 已初始化")

    @staticmethod
    def _detect_encoding(file_path: str) -> str:
        """检测文件编码。

        依次尝试候选编码，返回第一个能正确解码的编码。

        Args:
            file_path: 文本文件路径。

        Returns:
            检测到的编码名称。

        Raises:
            UnicodeDecodeError: 所有候选编码均失败时抛出。
        """
        raw_bytes = Path(file_path).read_bytes()
        for encoding in _CANDIDATE_ENCODINGS:
            try:
                raw_bytes.decode(encoding)
                logger.debug(f"文件编码检测成功: {encoding} ({file_path})")
                return encoding
            except UnicodeDecodeError:
                continue
        # 全部失败，使用 utf-8 抛出原始异常
        logger.error(f"无法识别文件编码: {file_path}")
        raise UnicodeDecodeError(
            "utf-8", raw_bytes, 0, 1, "无法以 UTF-8/GBK 等编码解码文件"
        )

    def _read_text(self, file_path: str) -> str:
        """以检测到的编码读取文件全文。"""
        path = Path(file_path)
        if not path.exists():
            logger.error(f"TXT 文件不存在: {file_path}")
            raise FileNotFoundError(f"TXT 文件不存在: {file_path}")
        encoding = self._detect_encoding(file_path)
        return path.read_text(encoding=encoding)

    def extract_text(self, file_path: str) -> str:
        """读取文本文件全部内容。

        Args:
            file_path: 文本文件路径。

        Returns:
            文件全部文本。
        """
        logger.info(f"开始读取 TXT 文件: {file_path}")
        text = self._read_text(file_path)
        logger.info(f"TXT 文件读取完成，共 {len(text)} 字符")
        return text

    def extract_lines(self, file_path: str) -> List[Dict]:
        """按行提取文本。

        Args:
            file_path: 文本文件路径。

        Returns:
            列表，元素为 ``{"line": int, "text": str}``，行号从 1 开始。
        """
        text = self._read_text(file_path)
        logger.info(f"开始按行切分 TXT: {file_path}")
        # splitlines 不会保留行尾换行符，且兼容 \r\n / \n / \r
        raw_lines = text.splitlines()
        results: List[Dict] = []
        for index, line in enumerate(raw_lines, start=1):
            results.append({"line": index, "text": line})
        logger.info(f"TXT 按行提取完成，共 {len(results)} 行")
        return results
