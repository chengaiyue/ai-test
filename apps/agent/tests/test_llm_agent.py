"""对话 Agent 测试：用 LangChain FakeListChatModel 离线验证 invoke / 流式。

不发起任何网络请求；FakeListChatModel 是标准 BaseChatModel，
会正常触发 LangGraph 的 messages 流式回调。
"""

import pytest
from agent.llm.agent import build_chat_agent, invoke_agent, stream_agent
from agent.llm.chat import chat, stream_chat
from langchain_core.language_models.fake_chat_models import FakeListChatModel

ANSWER = "这是来自火山引擎方舟大模型的流式回复，用于测试逐 token 输出。" * 2


@pytest.fixture
def fake_model():
    return FakeListChatModel(responses=[ANSWER] * 8)


def test_agent_invoke(fake_model):
    agent = build_chat_agent(fake_model)
    assert invoke_agent(agent, "你好") == ANSWER


def test_agent_stream_concats_to_full_answer(fake_model):
    agent = build_chat_agent(fake_model)
    chunks = list(stream_agent(agent, "你好"))
    assert len(chunks) > 1  # 确实是分多段产出的
    assert "".join(chunks) == ANSWER


class _RecordingModel(FakeListChatModel):
    """记录最近一次收到的消息，用于断言系统提示词被透传。"""

    responses: list[str] = [ANSWER]
    last_messages: list = []  # type: ignore[assignment]

    def invoke(self, messages, **kwargs):  # type: ignore[override]
        self.last_messages = list(messages)
        return super().invoke(messages, **kwargs)


def test_agent_system_prompt_passthrough():
    model = _RecordingModel()
    agent = build_chat_agent(model)
    assert invoke_agent(agent, "你好", system_prompt="你是测试助手") == ANSWER
    assert model.last_messages[0].type == "system"
    assert model.last_messages[0].content == "你是测试助手"
    assert model.last_messages[1].type == "human"


def test_direct_chat_wrapper(fake_model):
    assert chat("你好", model=fake_model) == ANSWER
    assert "".join(stream_chat("你好", model=fake_model)) == ANSWER
