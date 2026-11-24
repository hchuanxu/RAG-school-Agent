"""混合检索器。

支持跨多个 ChromaDB 集合（知识库）的语义检索，并归一化返回结果。
"""
from typing import Any, Dict, List, Optional

from loguru import logger

from app.rag.embeddings.embedding_factory import EmbeddingFactory
from app.rag.vectorstore.chroma_manager import ChromaManager


class HybridRetriever:
    """混合检索器。

    Args:
        embedding_factory: Embedding 工厂实例。
        chroma_manager: ChromaDB 管理器实例。
    """

    def __init__(
        self,
        embedding_factory: EmbeddingFactory,
        chroma_manager: ChromaManager,
    ) -> None:
        self.embedding_factory = embedding_factory
        self.chroma_manager = chroma_manager
        logger.debug("HybridRetriever 已初始化")

    def _normalize_results(
        self,
        raw: Dict[str, Any],
        knowledge_base: str,
    ) -> List[Dict]:
        """将 ChromaDB 原始结果归一化为统一结构。

        Args:
            raw: ChromaDB query 返回的字典。
            knowledge_base: 当前检索的集合名称。

        Returns:
            归一化结果列表。
        """
        normalized: List[Dict] = []
        # ChromaDB 返回结构：每个键的值是按 query 分组的二维列表
        documents_list = raw.get("documents", []) or []
        metadatas_list = raw.get("metadatas", []) or []
        distances_list = raw.get("distances", []) or []
        ids_list = raw.get("ids", []) or []

        for group_idx, doc_group in enumerate(documents_list):
            meta_group = (
                metadatas_list[group_idx]
                if group_idx < len(metadatas_list)
                else []
            )
            dist_group = (
                distances_list[group_idx]
                if group_idx < len(distances_list)
                else []
            )

            for item_idx, content in enumerate(doc_group or []):
                metadata = (
                    meta_group[item_idx]
                    if item_idx < len(meta_group)
                    else {}
                ) or {}
                distance = (
                    dist_group[item_idx]
                    if item_idx < len(dist_group)
                    else None
                )
                # ChromaDB 默认返回距离，越小越相似；转换为相似度分数
                score: Optional[float] = None
                if distance is not None:
                    try:
                        score = 1.0 - float(distance)
                    except (TypeError, ValueError):
                        score = None

                normalized.append(
                    {
                        "content": content,
                        "metadata": metadata,
                        "score": score,
                        "file_name": metadata.get("file_name", ""),
                        "page": metadata.get("page"),
                        "paragraph": metadata.get("paragraph"),
                        "knowledge_base": knowledge_base,
                    }
                )
        return normalized

    def retrieve(
        self,
        query: str,
        collection_names: List[str],
        top_k: int = 5,
    ) -> List[Dict]:
        """跨多个知识库检索。

        对每个集合分别检索 ``top_k`` 条结果，合并后按分数降序排序，
        取整体前 ``top_k`` 条返回。

        Args:
            query: 用户查询文本。
            collection_names: 待检索的集合（知识库）名称列表。
            top_k: 每个集合的检索数与最终返回数，默认 5。

        Returns:
            列表，元素为
            ``{content, metadata, score, file_name, page, paragraph, knowledge_base}``。
        """
        if not query or not collection_names:
            logger.warning(
                f"非法检索参数: query 为空={not query}, "
                f"集合数为 {len(collection_names)}"
            )
            return []

        # 预计算查询向量：使用 EmbeddingFactory（Ollama）生成，
        # 避免触发 ChromaDB 默认 ONNX 嵌入模型下载（all-MiniLM-L6-v2）。
        # 文档入库时同样使用该 EmbeddingFactory，保证向量空间一致。
        query_embedding: Optional[List[float]] = None
        try:
            embedder = self.embedding_factory.get_embedder()
            query_embedding = embedder.embed_query(query)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                f"查询向量化失败，回退至 ChromaDB 文本检索: {exc}"
            )

        logger.info(
            f"混合检索: query={query!r}, 集合={collection_names}, top_k={top_k}, "
            f"use_embedding={query_embedding is not None}"
        )
        all_results: List[Dict] = []
        for collection_name in collection_names:
            try:
                raw = self.chroma_manager.query(
                    collection_name=collection_name,
                    query_text=query,
                    n_results=top_k,
                    query_embedding=query_embedding,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    f"集合 {collection_name} 检索失败，跳过: {exc}"
                )
                continue
            all_results.extend(
                self._normalize_results(raw, knowledge_base=collection_name)
            )

        # 按分数降序排序（None 排到末尾）
        all_results.sort(
            key=lambda x: (x.get("score") is None, -(x.get("score") or 0.0))
        )
        final = all_results[:top_k]
        logger.info(
            f"混合检索完成: 候选 {len(all_results)} 条，返回 {len(final)} 条"
        )
        return final
