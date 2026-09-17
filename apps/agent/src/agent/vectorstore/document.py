"""文档模型与内容指纹。

对外统一使用 LangChain 的 ``Document``，本模块只负责构造与查重所需的指纹。
"""

import hashlib
import re

from langchain_core.documents import Document

_WHITESPACE_RE = re.compile(r"\s+")

# Chroma 元数据值只接受 str / int / float / bool
_ALLOWED_METADATA_TYPES = (str, int, float, bool)


def normalize_content(content: str) -> str:
    """归一化文档内容：去掉首尾空白，并把连续空白压成单个空格。

    归一化后再算 hash，使「同一段文字、空白排版不同」仍被判定为重复文档。
    """
    return _WHITESPACE_RE.sub(" ", content.strip())


def content_hash(content: str) -> str:
    """文档内容指纹：对归一化文本取 SHA-256，返回十六进制字符串。"""
    return hashlib.sha256(normalize_content(content).encode("utf-8")).hexdigest()


def make_document(
    content: str,
    title: str | None = None,
    source: str | None = None,
    metadata: dict | None = None,
) -> Document:
    """构造一篇 LangChain ``Document``，清洗并合并元数据。

    元数据中的 None 值和不被 Chroma 支持的类型会被丢弃。
    """
    meta: dict = {}
    if title is not None:
        meta["title"] = str(title)
    if source is not None:
        meta["source"] = str(source)
    for key, value in (metadata or {}).items():
        if value is None:
            continue
        if not isinstance(value, _ALLOWED_METADATA_TYPES):
            value = str(value)
        meta[key] = value
    return Document(page_content=content, metadata=meta)
