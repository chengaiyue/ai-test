"""向量库门面：封装 LangChain Chroma 向量存储与 LangGraph 工作流。"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import chromadb
from langchain_chroma import Chroma

from agent.vectorstore.chunker import make_splitter
from agent.vectorstore.embeddings import embedder_name, get_embeddings
from agent.vectorstore.graph import build_ingest_graph, build_query_graph

# 嵌入器标识中只保留 Chroma collection 名允许的字符
_COLLECTION_SANITIZE_RE = re.compile(r"[^A-Za-z0-9_-]+")


def default_store_path() -> Path:
    """向量库持久化目录：优先环境变量，否则 monorepo 根下 data/vector_store。"""
    env_path = os.environ.get("AGENT_VECTOR_STORE_PATH")
    if env_path:
        return Path(env_path)
    # 延迟导入：临时目录 / 独立运行场景下不依赖 monorepo 结构
    from common_utils.path_tool import get_abs_path

    return Path(get_abs_path("data/vector_store"))


def _collection_name(embeddings) -> str:
    profile = _COLLECTION_SANITIZE_RE.sub("_", embedder_name(embeddings)).strip("_")
    return f"docs_{profile}"[:63]


@dataclass
class AddResult:
    """一次批量入库的结果。"""

    added_hashes: list[str] = field(default_factory=list)
    duplicate_hashes: list[str] = field(default_factory=list)
    chunks_added: int = 0

    @property
    def added_count(self) -> int:
        return len(self.added_hashes)

    @property
    def duplicate_count(self) -> int:
        return len(self.duplicate_hashes)


@dataclass
class ScoredChunk:
    """带相似度分数的切片。"""

    content: str
    score: float
    metadata: dict


class VectorStore:
    """文档向量库：查重入库与相似度查询。

    Args:
        embeddings: LangChain Embeddings；默认按环境变量选择（本地哈希 / OpenAI 兼容）。
        path: 持久化目录；默认 ``<仓库根>/data/vector_store`` 或
            ``AGENT_VECTOR_STORE_PATH`` 环境变量。
        chunk_size / chunk_overlap: 切片参数。
    """

    def __init__(
        self,
        embeddings=None,
        path: str | Path | None = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        self.embeddings = embeddings or get_embeddings()
        self.path = Path(path) if path is not None else default_store_path()
        self.splitter = make_splitter(chunk_size, chunk_overlap)
        self.collection_name = _collection_name(self.embeddings)

        client_settings = chromadb.Settings(anonymized_telemetry=False)
        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(self.path),
            client_settings=client_settings,
        )
        self._collection = self.vectorstore._collection  # 查重 / 统计走底层批量接口

        self._ingest_graph = build_ingest_graph(self)
        self._query_graph = build_query_graph(self)

    # ------------------------------------------------------------------ 查重

    def existing_hashes(self, hashes: list[str]) -> set[str]:
        """返回给定指纹中，库里已经存在的那些（跨切片去重，只看文档指纹）。"""
        unique = list(dict.fromkeys(hashes))
        if not unique:
            return set()
        if len(unique) == 1:
            where: dict = {"doc_hash": unique[0]}
        else:
            where = {"doc_hash": {"$in": unique}}
        metadatas = self._collection.get(where=where, include=["metadatas"]).get(
            "metadatas", []
        )
        return {meta["doc_hash"] for meta in metadatas if meta and "doc_hash" in meta}

    # ------------------------------------------------------------------ 写入

    def add_documents(self, documents: list) -> AddResult:
        """经入库工作流处理一批文档：查重 → 切片 → 写入。

        重复文档（归一化后内容指纹相同）整体跳过，不产生任何切片。
        """
        if not documents:
            return AddResult()
        result = self._ingest_graph.invoke({"documents": list(documents)})
        new_hashes = [doc.metadata["doc_hash"] for doc in result["new_documents"]]
        return AddResult(
            added_hashes=new_hashes,
            duplicate_hashes=result.get("duplicate_hashes", []),
            chunks_added=len(result.get("chunk_ids", [])),
        )

    # ------------------------------------------------------------------ 查询

    def search(self, query: str, k: int = 5) -> list[ScoredChunk]:
        """语义相似度检索，返回最相关的 k 个切片（按相关度降序）。"""
        result = self._query_graph.invoke({"query": query, "k": k})
        return [
            ScoredChunk(
                content=item["content"],
                score=float(item["score"]),
                metadata=item["metadata"],
            )
            for item in result.get("results", [])
        ]

    # ------------------------------------------------------------------ 统计

    def stats(self) -> dict[str, int]:
        """返回当前嵌入空间下的文档数与切片数。"""
        data = self._collection.get(include=["metadatas"])
        hashes = {meta["doc_hash"] for meta in data.get("metadatas", []) if meta}
        return {"documents": len(hashes), "chunks": len(data.get("ids", []))}
