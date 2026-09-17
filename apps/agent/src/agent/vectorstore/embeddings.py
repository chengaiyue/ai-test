"""文本嵌入：可插拔的 LangChain Embeddings 实现。

- ``HashingEmbeddings``：本地零下载实现，字符 n-gram 特征哈希 + L2 归一化，
  确定性、离线可跑，中文按字重叠即可得到合理的粗粒度相似度（仅用于演示）。
- OpenAI 兼容嵌入：配置 ``OPENAI_API_KEY`` 后，``get_embeddings()`` 自动返回
  ``langchain_openai.OpenAIEmbeddings``（可通过 ``OPENAI_BASE_URL`` 指向兼容网关，
  通过 ``EMBEDDING_MODEL`` 选择模型）。
"""

import hashlib
import os

import numpy as np
from langchain_core.embeddings import Embeddings

_HASH_DIM = 512


class HashingEmbeddings(Embeddings):
    """字符 n-gram 特征哈希嵌入（本地、确定性、无需下载）。"""

    def __init__(self, dim: int = _HASH_DIM) -> None:
        self.dim = dim
        self.name = f"local-hash-v1-{dim}d"

    def _embed_one(self, text: str) -> np.ndarray:
        # 统一小写 + 首尾加边界符；unigram 兼顾短查询，bigram 承载词序信息
        normalized = f"^{text.strip().lower()}$"
        vector = np.zeros(self.dim, dtype=np.float32)
        if normalized == "^$":
            return vector
        features = list(normalized)
        features.extend(normalized[i : i + 2] for i in range(len(normalized) - 1))
        for feature in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "little") % self.dim
            # 用哈希的第 5 个字节决定符号，降低特征碰撞造成的偏差
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign
        norm = np.linalg.norm(vector)
        return vector / norm if norm else vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text).tolist() for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_one(text).tolist()


def get_embeddings() -> Embeddings:
    """按环境变量选择嵌入器。

    配置了 ``OPENAI_API_KEY`` 时返回 OpenAI 兼容嵌入，否则返回零下载的本地嵌入。
    返回对象带 ``name`` 属性，用于区分 / 隔离不同的向量空间。
    """
    if os.environ.get("OPENAI_API_KEY"):
        # 延迟导入：没配 key 的纯本地场景不需要 openai SDK
        from langchain_openai import OpenAIEmbeddings

        model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
        kwargs: dict = {"model": model}
        if os.environ.get("OPENAI_BASE_URL"):
            kwargs["base_url"] = os.environ["OPENAI_BASE_URL"]
        embeddings = OpenAIEmbeddings(**kwargs)
        embeddings.name = f"openai-{model}"
        return embeddings
    return HashingEmbeddings()


def embedder_name(embeddings: Embeddings) -> str:
    """嵌入器标识：优先 name 属性，否则用类名。"""
    return getattr(embeddings, "name", embeddings.__class__.__name__)
