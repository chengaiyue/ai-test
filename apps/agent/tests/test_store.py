"""向量库端到端测试：切片入库、查重、相似度查询。"""

import pytest

from agent.vectorstore import VectorStore, chunk_text
from agent.vectorstore.document import content_hash, make_document
from agent.vectorstore.embeddings import HashingEmbeddings


@pytest.fixture
def store(tmp_path):
    return VectorStore(embeddings=HashingEmbeddings(), path=tmp_path / "vectordb", chunk_size=60)


def _long_doc(topic: str) -> str:
    # 足够长，保证一篇文档产生多个切片
    return "。".join(f"{topic}相关的第{i}段内容，包含关键词{topic}" for i in range(8)) + "。"


def test_add_documents_chunks_and_persists(store):
    result = store.add_documents([make_document(_long_doc("向量数据库"), title="向量库文档")])
    assert result.added_count == 1
    assert result.duplicate_count == 0
    assert result.chunks_added > 1
    assert store.stats()["documents"] == 1
    assert store.stats()["chunks"] == result.chunks_added


def test_duplicate_document_is_skipped(store):
    content = _long_doc("重复检测")
    first = store.add_documents([make_document(content, source="a.txt")])
    assert first.added_count == 1
    chunks_after_first = store.stats()["chunks"]

    # 同一篇文档再来一次：整体跳过，不新增任何切片
    second = store.add_documents([make_document(content, source="b.txt")])
    assert second.added_count == 0
    assert second.duplicate_count == 1
    assert second.chunks_added == 0
    assert store.stats()["chunks"] == chunks_after_first


def test_duplicate_detection_normalizes_whitespace(store):
    content = _long_doc("空白归一化")
    store.add_documents([make_document(content)])
    # 首尾空白、换行、制表符不同，归一化（strip + 压缩空白）后指纹相同
    variant = f"\n\t {content}  \n"
    result = store.add_documents([make_document(variant)])
    assert result.duplicate_count == 1
    assert content_hash(content) == content_hash(variant)


def test_semantic_search_finds_relevant_chunk(store):
    store.add_documents(
        [
            make_document(_long_doc("向量数据库"), source="vector.txt"),
            make_document(_long_doc("天气预报"), source="weather.txt"),
        ]
    )
    hits = store.search("向量数据库的相似度怎么算", k=2)
    assert hits
    assert "向量数据库" in hits[0].content
    assert hits[0].metadata["source"] == "vector.txt"
    assert 0.0 <= hits[0].score <= 1.0001


def test_persistence_across_connections(tmp_path):
    path = tmp_path / "vectordb"
    store1 = VectorStore(embeddings=HashingEmbeddings(), path=path, chunk_size=60)
    store1.add_documents([make_document(_long_doc("持久化"))])

    # 重新打开同一目录，数据仍在，重复添加仍被拦截
    store2 = VectorStore(embeddings=HashingEmbeddings(), path=path, chunk_size=60)
    assert store2.stats()["documents"] == 1
    assert store2.add_documents([make_document(_long_doc("持久化"))]).duplicate_count == 1


def test_different_embedders_use_isolated_collections(tmp_path):
    local_store = VectorStore(embeddings=HashingEmbeddings(), path=tmp_path / "db")
    assert local_store.collection_name == "docs_local-hash-v1-512d"
    local_store.add_documents([make_document(_long_doc("隔离测试"))])

    class OtherEmbedder(HashingEmbeddings):
        def __init__(self):
            super().__init__(dim=128)

    other_store = VectorStore(embeddings=OtherEmbedder(), path=tmp_path / "db")
    assert other_store.collection_name != local_store.collection_name
    assert other_store.stats()["documents"] == 0


def test_chunk_text_helper_keeps_chinese_boundaries():
    text = "。".join(f"这是关于知识库的第{i}句话" for i in range(6))
    chunks = chunk_text(text, chunk_size=30, chunk_overlap=5)
    assert len(chunks) > 1
    assert all("知识库" in chunk for chunk in chunks)
