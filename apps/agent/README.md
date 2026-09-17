# agent

基于 **LangChain + LangGraph + Chroma** 的向量数据库示例应用，提供文档入库（切片）、
内容指纹查重与语义相似度查询。

## 实现逻辑

- **切片**：LangChain `RecursiveCharacterTextSplitter`，按 `段落 → 行 → 中文句号 →
  英文句号 → 空格 → 逐字符` 递归切分，默认 500 字 / 50 字重叠（中文友好）。
- **查重**：对归一化文本（strip + 压缩空白）算 SHA-256 指纹；入库前批量查库，
  重复文档整体跳过，不产生任何切片。切片 id 为 `内容指纹:序号`，天然幂等。
- **查询**：Chroma 持久化向量库 + 余弦相似度检索。
- **编排**：以上步骤由两张 LangGraph 工作流驱动：
  - 入库：`查重 → 切片 → 持久化`
  - 查询：`归一化 → 检索`
- **嵌入可插拔**：
  - 默认 `HashingEmbeddings`：字符 n-gram 特征哈希（512 维，L2 归一化），
    **零下载、离线可跑、确定性**，适合演示；
  - 配置 `OPENAI_API_KEY` 后自动切换为 OpenAI 兼容嵌入（可经 `OPENAI_BASE_URL`
    指向兼容网关，用 `EMBEDDING_MODEL` 选模型）。
  - 不同嵌入器的数据按 collection 隔离（`docs_<embedder>`），不会混检。

数据持久化在仓库根的 `data/vector_store/`（已 gitignore），可用环境变量
`AGENT_VECTOR_STORE_PATH` 覆盖。

## CLI 用法

在仓库根目录执行：

```bash
# 添加文档（一个或多个文本文件）
uv run agent add docs/intro.txt docs/more.txt --title 简介

# 直接添加文本（可重复 --text）
uv run agent add --text "向量数据库支持文档切片、查重和语义检索。"

# 重复添加同样的内容会提示：跳过重复文档 1 篇
uv run agent add --text "向量数据库支持文档切片、查重和语义检索。"

# 语义查询
uv run agent search "怎么做相似度检索" -k 3

# 查看库内文档 / 切片数量
uv run agent stats
```

## Python API

```python
from agent.vectorstore import Document  # 复用 langchain_core.documents.Document
from agent.vectorstore import VectorStore, make_document

store = VectorStore()  # 默认本地嵌入，路径 data/vector_store
result = store.add_documents(
    [
        make_document("文档正文……", title="标题", source="intro.txt"),
    ]
)
print(result.added_count, result.duplicate_count, result.chunks_added)

for hit in store.search("查询内容", k=3):
    print(hit.score, hit.metadata["source"], hit.content[:80])
```
