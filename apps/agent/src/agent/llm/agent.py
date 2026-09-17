"""LangGraph 对话 Agent：调用火山引擎方舟大模型，支持流式输出。

工作流::

    用户消息 → [chat 模型节点] → AI 回复

非流式用编译图的 ``invoke`` 取完整回复；流式用 ``stream_mode="messages"``，
LangGraph 会把模型节点产出的 token 以 ``AIMessageChunk`` 逐段推送。
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from langchain_core.messages import AIMessageChunk, BaseMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from agent.config import LLMConfig
from agent.llm.chat import build_messages, get_chat_model


class ChatState(TypedDict, total=False):
    """对话图状态：消息列表由 add_messages 归并更新。"""

    messages: Annotated[list[BaseMessage], add_messages]


def build_chat_agent(
    model=None,
    *,
    config: LLMConfig | None = None,
):
    """编译对话 Agent 图。

    Args:
        model: 已构造的聊天模型；缺省时按配置文件创建火山方舟 ChatOpenAI。
        config: 大模型配置；缺省时从配置文件加载。
    """
    chat_model = model or get_chat_model(config)

    def chat_node(state: ChatState) -> dict:
        """调用大模型，把 AI 回复追加到消息列表。"""
        return {"messages": [chat_model.invoke(state["messages"])]}

    graph = StateGraph(ChatState)
    graph.add_node("chat", chat_node)
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)
    return graph.compile()


def invoke_agent(
    agent,
    question: str,
    *,
    system_prompt: str | None = None,
) -> str:
    """非流式运行 Agent，返回完整回复文本。"""
    result = agent.invoke({"messages": build_messages(question, system_prompt)})
    return result["messages"][-1].content


def stream_agent(
    agent,
    question: str,
    *,
    system_prompt: str | None = None,
) -> Iterator[str]:
    """流式运行 Agent，逐 token 产出回复文本。

    思维模型在推理阶段的 ``reasoning_content`` 不计入产出，只流式输出正式回复。
    """
    stream = agent.stream(
        {"messages": build_messages(question, system_prompt)},
        stream_mode="messages",
    )
    for chunk, _metadata in stream:
        if isinstance(chunk, AIMessageChunk) and isinstance(chunk.content, str) and chunk.content:
            yield chunk.content
