"""检索节点。

使用 HybridRetriever 跨知识库检索，并对检索器做懒加载单例缓存。
"""
import time
from typing import Any, Dict, List

from loguru import logger

from app.agents.state import AgentState


# 检索器单例（懒加载）
_retriever = None


def _get_retriever():
    """获取 HybridRetriever 单例。"""
    global _retriever
    if _retriever is None:
        try:
            from app.rag.embeddings.embedding_factory import EmbeddingFactory
            from app.rag.retrievers.hybrid_retriever import HybridRetriever
            from app.rag.vectorstore.chroma_manager import ChromaManager

            embedding_factory = EmbeddingFactory()
            chroma_manager = ChromaManager()
            _retriever = HybridRetriever(
                embedding_factory=embedding_factory,
                chroma_manager=chroma_manager,
            )
            logger.info("HybridRetriever 单例已创建")
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"创建 HybridRetriever 失败: {exc}")
            _retriever = None
    return _retriever


def retrieve_documents(state: AgentState) -> Dict[str, Any]:
    """检索节点。"""
    start = time.perf_counter()
    question = state.get("question", "")
    knowledge_base_ids: List[str] = state.get("knowledge_base_ids") or []

    # 使用 chat_service 解析的集合名列表
    collections = list(knowledge_base_ids) if knowledge_base_ids else []

    if not collections:
        logger.warning("未指定知识库集合，检索将返回空结果")
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {"retrieved_docs": [], "no_relevant_docs": True, "retrieval_latency_ms": latency_ms}

    retriever = _get_retriever()
    if retriever is None:
        logger.error("检索器不可用，标记为无相关文档")
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {"retrieved_docs": [], "no_relevant_docs": True, "retrieval_latency_ms": latency_ms}

    try:
        docs = retriever.retrieve(
            query=question, collection_names=collections, top_k=5
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"检索异常: {exc}")
        docs = []

    no_relevant = len(docs) == 0
    logger.info(f"检索完成: 搜索 {len(collections)} 个集合, 返回 {len(docs)} 条, no_relevant_docs={no_relevant}")
    latency_ms = int((time.perf_counter() - start) * 1000)
    return {"retrieved_docs": docs, "no_relevant_docs": no_relevant, "retrieval_latency_ms": latency_ms}
