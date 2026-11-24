"""PDF 文档解析器。

基于 PyPDF2 提取 PDF 文本内容，支持按页提取与中文编码处理。
"""
from pathlib import Path
from typing import Dict, List

from loguru import logger
from PyPDF2 import PdfReader


class PDFProcessor:
    """PDF 文档解析器。

    提供全文提取与按页提取能力，自动处理中文编码。
    """

    SUPPORTED_EXT = ".pdf"

    def __init__(self) -> None:
        logger.debug("PDFProcessor 已初始化")

    @staticmethod
    def _decode_text(text: str) -> str:
        """处理 PDF 文本中可能出现的编码问题。

        Args:
            text: 原始文本。

        Returns:
            处理后的文本。
        """
        if not text:
            return ""
        # 替换常见乱码占位符与无效字符
        try:
            # 去除 CJK 编码下可能出现的替换字符
            text = text.replace("\ufffd", "")
        except Exception:  # noqa: BLE001
            pass
        return text

    def extract_text(self, file_path: str) -> str:
        """提取 PDF 全部文本内容。

        Args:
            file_path: PDF 文件路径。

        Returns:
            合并后的全部文本。
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"PDF 文件不存在: {file_path}")
            raise FileNotFoundError(f"PDF 文件不存在: {file_path}")

        logger.info(f"开始提取 PDF 文本: {file_path}")
        reader = PdfReader(str(path))
        pages_text: List[str] = []
        for page in reader.pages:
            try:
                raw = page.extract_text() or ""
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"页面文本提取失败: {exc}")
                raw = ""
            pages_text.append(self._decode_text(raw))

        full_text = "\n".join(pages_text)
        logger.info(f"PDF 文本提取完成，共 {len(reader.pages)} 页，{len(full_text)} 字符")
        return full_text

    def extract_pages(self, file_path: str) -> List[Dict]:
        """按页提取 PDF 文本。

        Args:
            file_path: PDF 文件路径。

        Returns:
            列表，元素为 ``{"page": int, "text": str}``，页码从 1 开始。
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"PDF 文件不存在: {file_path}")
            raise FileNotFoundError(f"PDF 文件不存在: {file_path}")

        logger.info(f"开始按页提取 PDF 文本: {file_path}")
        reader = PdfReader(str(path))
        results: List[Dict] = []
        for index, page in enumerate(reader.pages, start=1):
            try:
                raw = page.extract_text() or ""
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"第 {index} 页文本提取失败: {exc}")
                raw = ""
            results.append(
                {
                    "page": index,
                    "text": self._decode_text(raw),
                }
            )
        logger.info(f"PDF 按页提取完成，共 {len(results)} 页")
        return results
