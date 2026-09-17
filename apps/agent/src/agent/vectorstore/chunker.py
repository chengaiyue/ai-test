"""文档切片：基于 LangChain RecursiveCharacterTextSplitter 的中文友好配置。"""

from langchain_text_splitters import RecursiveCharacterTextSplitter

# 分隔符从「语义最强」到「最弱」排列；中文句读（。！？）在英文标点之前，
# 空格与逐字符作为兜底，保证超长文本也能被切开。
DEFAULT_SEPARATORS = ["\n\n", "\n", "。", "！", "？", ". ", "! ", "? ", " ", ""]


def make_splitter(
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    separators: list[str] | None = None,
) -> RecursiveCharacterTextSplitter:
    """创建递归文本切片器（按字符数计长，中文友好）。"""
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap 必须小于 chunk_size")
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators if separators is not None else list(DEFAULT_SEPARATORS),
        length_function=len,
        keep_separator="start",
    )


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    separators: list[str] | None = None,
) -> list[str]:
    """把长文档切成带重叠的小片段。

    Args:
        text: 原文。
        chunk_size: 每个切片的最大字符数（按字符计，中文友好）。
        chunk_overlap: 相邻切片之间重叠的字符数，须小于 chunk_size。
        separators: 自定义分隔符优先级列表。

    Returns:
        切片文本列表；空白文本返回空列表。
    """
    if not text or not text.strip():
        return []
    return make_splitter(chunk_size, chunk_overlap, separators).split_text(text.strip())
