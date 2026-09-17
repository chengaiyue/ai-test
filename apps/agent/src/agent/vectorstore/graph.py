"""LangGraph 工作流：把入库 / 查询编排成有向图。

入库流水线（ingest）：
    输入文档 → [查重] → 新文档 [切片] → 切片 [持久化] → 向量库
                       └→ 重复文档直接跳过

查询流水线（query）：
    查询语句 → [归一化] → [向量检索] → 带分数的切片列表
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langchain_core.documents import Document
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from agent.vectorstore.document import content_hash, normalize_content

if TYPE_CHECKING:
    from agent.vectorstore.store import VectorStore


class IngestState(TypedDict, total=False):
    """入库流水线状态。"""

    documents: list[Document]
    new_documents: list[Document]
    duplicate_hashes: list[str]
    chunks: list[Document]
    chunk_ids: list[str]


class QueryState(TypedDict, total=False):
    """查询流水线状态。"""

    query: str
    k: int
    results: list[dict[str, Any]]


def build_ingest_graph(store: VectorStore):
    """编译入库工作流：查重 → 切片 → 持久化。"""

    def dedupe(state: IngestState) -> IngestState:
        """计算内容指纹，已存在的文档标记为重复并跳过。"""
        documents = state["documents"]
        hashes = [content_hash(doc.page_content) for doc in documents]
        existing = store.existing_hashes(hashes)

        new_documents: list[Document] = []
        duplicate_hashes: list[str] = []
        for doc, doc_hash in zip(documents, hashes):
            if doc_hash in existing:
                duplicate_hashes.append(doc_hash)
                continue
            doc.metadata["doc_hash"] = doc_hash
            new_documents.append(doc)
        return {"new_documents": new_documents, "duplicate_hashes": duplicate_hashes}

    def split(state: IngestState) -> IngestState:
        """对新文档逐篇切片，记录所属文档与切片序号。"""
        chunks: list[Document] = []
        chunk_ids: list[str] = []
        for doc in state["new_documents"]:
            doc_hash = doc.metadata["doc_hash"]
            for index, chunk in enumerate(store.splitter.split_documents([doc])):
                chunk.metadata["chunk_index"] = index
                chunks.append(chunk)
                chunk_ids.append(f"{doc_hash}:{index:04d}")
        return {"chunks": chunks, "chunk_ids": chunk_ids}

    def persist(state: IngestState) -> IngestState:
        """把切片写入向量库（同内容切片的 id 确定，天然幂等）。"""
        chunks = state.get("chunks", [])
        if chunks:
            store.vectorstore.add_documents(chunks, ids=state["chunk_ids"])
        return {}

    graph = StateGraph(IngestState)
    graph.add_node("dedupe", dedupe)
    graph.add_node("split", split)
    graph.add_node("persist", persist)
    graph.add_edge(START, "dedupe")
    graph.add_edge("dedupe", "split")
    graph.add_edge("split", "persist")
    graph.add_edge("persist", END)
    return graph.compile()


def build_query_graph(store: VectorStore):
    """编译查询工作流：归一化 → 检索。"""

    def normalize(state: QueryState) -> QueryState:
        query = state["query"].strip()
        if not query:
            raise ValueError("查询内容不能为空")
        return {"query": normalize_content(query)}

    def retrieve(state: QueryState) -> QueryState:
        hits = store.vectorstore.similarity_search_with_relevance_scores(
            state["query"], k=state.get("k", 5)
        )
        return {
            "results": [
                {"content": doc.page_content, "score": score, "metadata": doc.metadata}
                for doc, score in hits
            ]
        }

    graph = StateGraph(QueryState)
    graph.add_node("normalize", normalize)
    graph.add_node("retrieve", retrieve)
    graph.add_edge(START, "normalize")
    graph.add_edge("normalize", "retrieve")
    graph.add_edge("retrieve", END)
    return graph.compile()
