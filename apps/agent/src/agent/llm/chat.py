"""火山引擎方舟大模型调用：ChatOpenAI（OpenAI 兼容协议）封装。

Agent Plan 地址 ``/api/plan/v3`` 与标准推理地址 ``/api/v3`` 一样兼容 OpenAI 协议，
因此直接使用 ``langchain_openai.ChatOpenAI``，通过配置文件切换 base_url / 模型 / 密钥。
"""

from __future__ import annotations

from collections.abc import Iterator

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agent.config import LLMConfig, load_config


def get_chat_model(config: LLMConfig | None = None) -> ChatOpenAI:
    """按配置构造火山方舟聊天模型。"""
    config = config or load_config()
    kwargs: dict = {
        "model": config.model,
        "base_url": config.base_url,
        "api_key": config.api_key,
        "temperature": config.temperature,
    }
    if config.max_tokens is not None:
        kwargs["max_tokens"] = config.max_tokens
    return ChatOpenAI(**kwargs)


def build_messages(
    question: str, system_prompt: str | None = None
) -> list[BaseMessage]:
    """把系统提示词与用户问题组装成 LangChain 消息列表。"""
    messages: list[BaseMessage] = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=question))
    return messages


def _text_content(chunk) -> str:
    """只取文本片段；思维模型在推理阶段 content 为空，推理内容在 reasoning_content。"""
    content = chunk.content
    return content if isinstance(content, str) else ""


def chat(
    question: str,
    *,
    system_prompt: str | None = None,
    config: LLMConfig | None = None,
    model: ChatOpenAI | None = None,
) -> str:
    """一次性调用，返回完整回复文本。"""
    chat_model = model or get_chat_model(config)
    response = chat_model.invoke(build_messages(question, system_prompt))
    return _text_content(response)


def stream_chat(
    question: str,
    *,
    system_prompt: str | None = None,
    config: LLMConfig | None = None,
    model: ChatOpenAI | None = None,
) -> Iterator[str]:
    """流式调用，逐段产出回复文本（思维链片段不产出）。"""
    chat_model = model or get_chat_model(config)
    for chunk in chat_model.stream(build_messages(question, system_prompt)):
        text = _text_content(chunk)
        if text:
            yield text
