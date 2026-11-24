"""ChromaDB 管理器。

封装 ChromaDB 持久化客户端，提供集合管理与文档增删查接口。
当 chromadb 不可用时自动降级为内存向量存储。
"""
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from app.config import settings

# 尝试导入 chromadb
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("chromadb 未安装，将使用内存向量存储作为后备方案")


class _InMemoryCollection:
    """内存集合，模拟 ChromaDB Collection 接口。"""

    def __init__(self, name: str):
        self.name = name
        self._data: Dict[str, dict] = {}  # id -> {document, metadata, embedding}

    def add(self, documents, metadatas, ids, embeddings=None):
        for i, doc_id in enumerate(ids):
            self._data[doc_id] = {
                "document": documents[i],
                "metadata": metadatas[i] if metadatas else {},
                "embedding": embeddings[i] if embeddings else None,
            }

    def delete(self, where=None):
        if where is None:
            self._data.clear()
            return
        to_delete = []
        for doc_id, item in self._data.items():
            match = all(item["metadata"].get(k) == v for k, v in where.items())
            if match:
                to_delete.append(doc_id)
        for doc_id in to_delete:
            del self._data[doc_id]

    def count(self):
        return len(self._data)

    def query(self, query_texts=None, query_embeddings=None, n_results=5):
        """简单的关键词匹配检索（无向量相似度时的后备）。"""
        if not query_texts or not self._data:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}

        query_text = query_texts[0].lower()
        scored = []
        for doc_id, item in self._data.items():
            doc = item["document"].lower()
            # 简单的关键词重叠评分
            query_words = set(query_text.split())
            doc_words = set(doc.split())
            overlap = len(query_words & doc_words)
            score = overlap / max(len(query_words), 1) if query_words else 0
            scored.append((score, doc_id, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:n_results]

        return {
            "documents": [[s[2]["document"] for s in top]],
            "metadatas": [[s[2]["metadata"] for s in top]],
            "distances": [[1 - s[0] for s in top]],
            "ids": [[s[1] for s in top]],
        }


class _InMemoryClient:
    """内存客户端，模拟 ChromaDB PersistentClient 接口。"""

    def __init__(self):
        self._collections: Dict[str, _InMemoryCollection] = {}

    def get_or_create_collection(self, name: str):
        if name not in self._collections:
            self._collections[name] = _InMemoryCollection(name)
        return self._collections[name]

    def delete_collection(self, name: str):
        self._collections.pop(name, None)

    def get_collection(self, name: str):
        if name not in self._collections:
            raise ValueError(f"集合 {name} 不存在")
        return self._collections[name]


class ChromaManager:
    """ChromaDB 管理器（带内存后备）。

    Args:
        persist_dir: ChromaDB 持久化目录。
    """

    def __init__(self, persist_dir: Optional[str] = None) -> None:
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        if CHROMADB_AVAILABLE:
            logger.info(f"初始化 ChromaDB 持久化客户端: {self.persist_dir}")
            self.client = chromadb.PersistentClient(path=self.persist_dir)
        else:
            logger.warning("使用内存向量存储（数据不持久化）")
            self.client = _InMemoryClient()

    def create_collection(self, collection_name: str):
        """创建（如不存在则创建）并返回集合。"""
        logger.info(f"创建集合: {collection_name}")
        return self.client.get_or_create_collection(name=collection_name)

    def delete_collection(self, collection_name: str) -> None:
        """删除集合。"""
        logger.info(f"删除集合: {collection_name}")
        try:
            self.client.delete_collection(name=collection_name)
        except Exception as exc:
            logger.warning(f"删除集合失败（可能不存在）: {collection_name} - {exc}")

    def _get_collection(self, collection_name: str):
        """获取已存在的集合。"""
        return self.client.get_collection(name=collection_name)

    def add_documents(
        self,
        collection_name: str,
        texts: List[str],
        metadatas: List[Dict],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None,
    ) -> None:
        """向集合添加文档。"""
        if not (len(texts) == len(metadatas) == len(ids)):
            raise ValueError("texts / metadatas / ids 长度不一致")

        if embeddings is not None and len(embeddings) != len(texts):
            raise ValueError("embeddings 与 texts 长度不一致")

        if not texts:
            return

        collection = self.create_collection(collection_name)
        if embeddings is not None:
            collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings,
            )
        else:
            collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids,
            )
        logger.info(f"向集合 {collection_name} 添加 {len(texts)} 条文档")

    def delete_by_metadata(
        self,
        collection_name: str,
        metadata_key: str,
        metadata_value: str,
    ) -> None:
        """按元数据条件删除文档。"""
        logger.info(f"按元数据删除: 集合={collection_name}, {metadata_key}={metadata_value}")
        try:
            collection = self._get_collection(collection_name)
        except Exception as exc:
            logger.warning(f"集合不存在，跳过删除: {collection_name} - {exc}")
            return
        collection.delete(where={metadata_key: metadata_value})

    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        query_embedding: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """检索集合。

        优先使用预计算的 ``query_embedding``（由 EmbeddingFactory 生成），
        避免触发 ChromaDB 默认 ONNX 嵌入模型的下载与推理。
        """
        logger.debug(f"检索集合 {collection_name}: n_results={n_results}")
        collection = self._get_collection(collection_name)
        if query_embedding is not None:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
            )
        else:
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
            )
        return results

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """获取集合统计信息。"""
        try:
            collection = self._get_collection(collection_name)
        except Exception:
            return {"name": collection_name, "count": 0, "metadata": None}

        try:
            count = collection.count()
        except Exception:
            count = 0

        return {
            "name": collection_name,
            "count": count,
            "metadata": None,
        }
