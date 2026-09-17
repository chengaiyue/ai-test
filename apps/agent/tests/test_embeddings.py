"""本地哈希嵌入器测试。"""

import math

from agent.vectorstore.embeddings import HashingEmbeddings, embedder_name


def test_embedding_dimension_and_norm():
    embeddings = HashingEmbeddings(dim=256)
    vectors = embeddings.embed_documents(["向量数据库", ""])
    assert len(vectors) == 2
    assert all(len(v) == 256 for v in vectors)
    assert math.isclose(math.sqrt(sum(x * x for x in vectors[0])), 1.0, rel_tol=1e-5)
    # 空文本得到零向量
    assert all(x == 0.0 for x in vectors[1])


def test_embedding_is_deterministic():
    embeddings = HashingEmbeddings()
    first = embeddings.embed_query("同一段文本")
    second = embeddings.embed_query("同一段文本")
    assert first == second


def test_similar_texts_have_higher_cosine():
    embeddings = HashingEmbeddings()

    def cosine(a: str, b: str) -> float:
        va, vb = embeddings.embed_query(a), embeddings.embed_query(b)
        return sum(x * y for x, y in zip(va, vb))

    related = cosine("向量数据库的相似度检索", "向量数据库检索")
    unrelated = cosine("向量数据库的相似度检索", "今天晴朗适合出门散步")
    assert related > unrelated


def test_embedder_name():
    assert embedder_name(HashingEmbeddings()) == "local-hash-v1-512d"

    class Named:
        name = "custom"

    assert embedder_name(Named()) == "custom"
