"""Word 文档解析器。

基于 python-docx 提取 .docx 段落文本，识别标题层级。
"""
from pathlib import Path
from typing import Dict, List

from docx import Document
from loguru import logger


class DOCXProcessor:
    """Word 文档解析器。

    按段落提取文本，并标记是否为标题。
    """

    SUPPORTED_EXT = ".docx"

    def __init__(self) -> None:
        logger.debug("DOCXProcessor 已初始化")

    @staticmethod
    def _is_heading(paragraph) -> bool:
        """判断段落是否为标题。

        Args:
            paragraph: python-docx 段落对象。

        Returns:
            是标题返回 True，否则 False。
        """
        style_name = ""
        try:
            style_name = paragraph.style.name or ""
        except Exception:  # noqa: BLE001
            return False
        # Heading 1 ~ Heading 9 以及 Title
        return style_name.startswith("Heading") or style_name == "Title"

    def extract_paragraphs(self, file_path: str) -> List[Dict]:
        """提取 Word 文档段落。

        Args:
            file_path: .docx 文件路径。

        Returns:
            列表，元素为
            ``{"paragraph": int, "text": str, "is_heading": bool}``，
            段落序号从 1 开始。
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"DOCX 文件不存在: {file_path}")
            raise FileNotFoundError(f"DOCX 文件不存在: {file_path}")

        logger.info(f"开始提取 DOCX 段落: {file_path}")
        document = Document(str(path))
        results: List[Dict] = []
        for index, paragraph in enumerate(document.paragraphs, start=1):
            text = (paragraph.text or "").strip()
            if not text:
                # 保留空段落位置信息以便还原结构，但标记为非标题
                results.append(
                    {
                        "paragraph": index,
                        "text": "",
                        "is_heading": False,
                    }
                )
                continue
            results.append(
                {
                    "paragraph": index,
                    "text": text,
                    "is_heading": self._is_heading(paragraph),
                }
            )
        logger.info(f"DOCX 段落提取完成，共 {len(results)} 段")
        return results
