"""大模型对话模块：火山引擎方舟 Agent Plan（OpenAI 兼容）+ LangGraph。

公开接口：

- ``LLMConfig`` / ``load_config``：TOML 配置；
- ``get_chat_model``：构造方舟 ChatOpenAI；
- ``chat`` / ``stream_chat``：直连模型的一次性 / 流式调用；
- ``build_chat_agent`` / ``invoke_agent`` / ``stream_agent``：LangGraph 对话 Agent。
"""

from agent.config import LLMConfig, load_config
from agent.llm.agent import (
    build_chat_agent,
    invoke_agent,
    stream_agent,
)
from agent.llm.chat import chat, get_chat_model, stream_chat

__all__ = [
    "LLMConfig",
    "load_config",
    "get_chat_model",
    "chat",
    "stream_chat",
    "build_chat_agent",
    "invoke_agent",
    "stream_agent",
]
