# agent

基于 **LangChain + LangGraph + Chroma** 的示例应用：

- **向量数据库**：文档入库（切片）、内容指纹查重与语义相似度查询；
- **大模型对话**：调用火山引擎方舟 Agent Plan（OpenAI 兼容协议），由 LangGraph 编排，
  支持逐 token 流式输出。

## 大模型配置

对话功能读取 `apps/agent/config.toml`（TOML 格式，使用 Python 标准库解析，无需额外依赖）：

```bash
cp apps/agent/config.example.toml apps/agent/config.toml
```

```toml
[llm]
base_url = "https://ark.cn-beijing.volces.com/api/plan/v3"  # Agent Plan 专属地址
api_key = "ark-你的密钥"                                      # 也可用环境变量 ARK_API_KEY
model = "doubao-seed-2.0-mini"                               # 套餐内模型 ID
temperature = 0.7
stream = true                                                # CLI 默认流式输出
```

说明：

- `config.toml` 含真实密钥，已在 `.gitignore` 中忽略；可提交的模板是
  `config.example.toml`。
- 配置文件查找顺序：环境变量 `AGENT_CONFIG_PATH` → `apps/agent/config.toml`
  → 当前目录 `./config.toml`。
- 可选模型见[方舟 Agent Plan 文档](https://www.volcengine.com/docs/82379/2366394)
  （Agent Plan 使用 `/api/plan/v3` 专属地址和专属 Key，与标准推理地址 `/api/v3` 不通用）。
- 思维模型推理阶段的 `reasoning_content` 不会作为回复流式输出，只输出正式回答。

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

# 与火山方舟大模型对话（默认逐 token 流式输出）
uv run agent chat "用一句话介绍向量检索"

# 非流式输出 / 自定义系统提示词
uv run agent chat "1+1=?" --no-stream --system "你只回答结果，不要解释"
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

大模型对话（配置读取 `config.toml`）：

```python
from agent.llm import build_chat_agent, invoke_agent, stream_agent

agent = build_chat_agent()                       # 火山方舟 ChatOpenAI（OpenAI 兼容）

print(invoke_agent(agent, "你好"))               # 一次性完整回复

for token in stream_agent(agent, "讲个小故事"):  # 逐 token 流式
    print(token, end="", flush=True)
```
