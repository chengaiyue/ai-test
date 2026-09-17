"""agent 应用：基于 LangChain + LangGraph 的向量数据库。

- 文档切片：LangChain RecursiveCharacterTextSplitter（中文友好分隔符）
- 文档查重：归一化内容 SHA-256 指纹，重复文档整体跳过
- 相似度查询：Chroma 持久化向量库 + 可插拔嵌入（本地哈希 / OpenAI 兼容 API）
- 流程编排：LangGraph（查重 → 切片 → 持久化；归一化 → 检索）
- 大模型对话：火山引擎方舟 Agent Plan（OpenAI 兼容），配置见 config.toml，支持流式输出
"""

from agent.cli import main

__all__ = ["main"]
