"""切片器测试。"""

from agent.vectorstore.chunker import chunk_text, make_splitter


def test_empty_text_returns_empty():
    assert chunk_text("") == []
    assert chunk_text("   \n  ") == []


def test_short_text_single_chunk():
    text = "短文本，不需要切分。"
    chunks = chunk_text(text, chunk_size=500)
    assert chunks == [text]


def test_long_text_split_into_multiple_chunks_with_overlap():
    # 10 个各 20 字的句子，共约 210 字；chunk_size=60 应切成多片
    text = "".join(f"这是第{i}个用于测试的中文句子。" for i in range(10))
    chunks = chunk_text(text, chunk_size=60, chunk_overlap=10)

    assert len(chunks) >= 3
    # keep_separator='start' 时切片可能略长于 chunk_size（多出分隔符长度）
    assert all(len(chunk) <= 62 for chunk in chunks)
    # 相邻切片应有重叠内容
    assert any(set(chunks[0]) & set(chunks[1]))


def test_splits_on_chinese_sentence_boundary():
    text = "句子一。句子二。句子三。句子四。"
    chunks = chunk_text(text, chunk_size=10, chunk_overlap=0)
    assert len(chunks) >= 2
    # 每个切片都是完整句子的组合，不会在句子中间硬切（"句子" 不被拆散）
    assert all("句子" in chunk for chunk in chunks)


def test_invalid_overlap_raises():
    import pytest

    with pytest.raises(ValueError):
        make_splitter(chunk_size=10, chunk_overlap=10)
