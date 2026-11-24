"""文档摘要生成器。

调用 LLM 基于 SUMMARY_PROMPT 生成 200-500 字的结构化摘要。
针对长文档采用截取前 4000 字的策略控制输入长度。
"""
from typing import Optional

from loguru import logger

from app.core.llm_factory import create_chat_llm
from app.rag.prompts.chat_prompts import SUMMARY_PROMPT


class DocumentSummarizer:
    """文档摘要生成器。"""

    # 输入文本最大字符数，超过则截取前 N 字
    MAX_INPUT_LENGTH = 4000

    def __init__(self) -> None:
        self._llm = None
        logger.debug("DocumentSummarizer 已初始化")

    def _get_llm(self):
        """懒加载获取 LLM 实例。"""
        if self._llm is None:
            self._llm = create_chat_llm()
        return self._llm

    async def generate_summary(
        self, document_text: str, title: Optional[str] = None
    ) -> str:
        """生成文档摘要。

        Args:
            document_text: 文档全文文本。
            title: 文档标题，用于上下文增强，可选。

        Returns:
            200-500 字的摘要文本；输入为空时返回空字符串。
        """
        if not document_text or not document_text.strip():
            logger.warning("文档内容为空，无法生成摘要")
            return ""

        # 长文档截取前 4000 字
        if len(document_text) > self.MAX_INPUT_LENGTH:
            logger.info(
                f"文档过长({len(document_text)}字)，截取前 {self.MAX_INPUT_LENGTH} 字生成摘要"
            )
            document_text = document_text[: self.MAX_INPUT_LENGTH]

        try:
            prompt = SUMMARY_PROMPT.format(
                title=title or "未命名文档", content=document_text
            )
            response = await self._get_llm().ainvoke(prompt)
            summary = (
                response.content if hasattr(response, "content") else str(response)
            )
            summary = (summary or "").strip()
            logger.info(f"摘要生成完成，长度 {len(summary)}")
            return summary
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"摘要生成失败: {exc}")
            raise


# 模块级单例
document_summarizer = DocumentSummarizer()
