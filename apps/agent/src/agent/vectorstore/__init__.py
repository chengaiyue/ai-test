"""向量数据库模块：文档切片、查重与相似度查询（LangChain + LangGraph + Chroma）。

公开接口：

- ``make_document`` / LangChain 的 ``Document``：构造待入库文档；
- ``chunk_text``：文档切片；
- ``get_embeddings``：按环境变量选择嵌入实现（本地哈希 / OpenAI 兼容 API）；
- ``VectorStore``：向量库门面（add_documents / search / stats）。
"""

from langchain_core.documents import Document

from agent.vectorstore.chunker import chunk_text
from agent.vectorstore.document import content_hash, make_document, normalize_content
from agent.vectorstore.embeddings import (
    HashingEmbeddings,
    embedder_name,
    get_embeddings,
)
from agent.vectorstore.store import AddResult, ScoredChunk, VectorStore

__all__ = [
    "Document",
    "make_document",
    "content_hash",
    "normalize_content",
    "chunk_text",
    "HashingEmbeddings",
    "get_embeddings",
    "embedder_name",
    "VectorStore",
    "AddResult",
    "ScoredChunk",
]
