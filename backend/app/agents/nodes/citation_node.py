"""溯源节点。

从检索结果构建 Citation 列表，提取文件名、页码、段落、分块索引等信息。
"""
from typing import Any, Dict, List

from loguru import logger

from app.agents.state import AgentState, Citation


# 内容预览最大长度
_PREVIEW_LEN = 100


def extract_citations(state: AgentState) -> Dict[str, Any]:
    """从检索结果构建引用列表。"""
    docs: List[dict] = state.get("retrieved_docs") or []
    citations: List[Citation] = []

    for idx, doc in enumerate(docs):
        metadata = doc.get("metadata") or {}
        content = doc.get("content") or ""
        preview = content[:_PREVIEW_LEN].replace("\n", " ").strip()

        score = doc.get("score")
        try:
            score_value = float(score) if score is not None else 0.0
        except (TypeError, ValueError):
            score_value = 0.0

        page = doc.get("page")
        if page is None:
            page = metadata.get("page")
        paragraph = doc.get("paragraph")
        if paragraph is None:
            paragraph = metadata.get("paragraph")

        citations.append(
            Citation(
                file_name=doc.get("file_name") or metadata.get("file_name", ""),
                page=page,
                paragraph=paragraph,
                chunk_index=metadata.get("chunk_index", idx),
                knowledge_base=doc.get("knowledge_base", ""),
                content_preview=preview,
                similarity_score=score_value,
            )
        )

    logger.info(f"构建引用列表: {len(citations)} 条")
    return {"citations": citations}
