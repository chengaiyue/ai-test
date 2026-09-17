"""CLI 冒烟测试：add（含查重）→ search → stats，以及大模型 chat。"""

import pytest
from agent.cli import main
from langchain_core.language_models.fake_chat_models import FakeListChatModel


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_VECTOR_STORE_PATH", str(tmp_path / "cli_db"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def test_cli_add_search_stats(capsys):
    text = "向量数据库支持文档切片、内容指纹查重和语义相似度检索。" * 5

    # 第一次添加
    assert main(["add", "--text", text, "--title", "功能说明"]) == 0
    out = capsys.readouterr().out
    assert "新增文档 1 篇" in out

    # 第二次添加相同文本 → 重复跳过
    assert main(["add", "--text", text]) == 0
    out = capsys.readouterr().out
    assert "跳过重复文档 1 篇" in out

    # 查询
    assert main(["search", "怎么查重", "-k", "2"]) == 0
    out = capsys.readouterr().out
    assert "向量数据库" in out
    assert "[1]" in out

    # 统计
    assert main(["stats"]) == 0
    out = capsys.readouterr().out
    assert "文档 1 篇" in out
    assert "切片" in out


def test_cli_chat_stream_and_non_stream(tmp_path, monkeypatch, capsys):
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        '[llm]\nbase_url = "https://ark.example.com/v3"\n'
        'api_key = "ark-test"\nmodel = "doubao-test"\nstream = true\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("AGENT_CONFIG_PATH", str(config_file))

    fake_model = FakeListChatModel(responses=["流式回复内容", "完整回复内容"])
    # build_chat_agent 从自身模块命名空间取 get_chat_model，替换掉以避免真实网络调用
    monkeypatch.setattr(
        "agent.llm.agent.get_chat_model", lambda config=None: fake_model
    )

    assert main(["chat", "你好"]) == 0
    out = capsys.readouterr().out
    assert "流式回复内容" in out

    assert main(["chat", "你好", "--no-stream"]) == 0
    out = capsys.readouterr().out
    assert "完整回复内容" in out


def test_cli_chat_missing_config(monkeypatch, tmp_path):
    # 显式指向不存在的配置：直接失败，不应回退到仓库内的真实 config.toml
    monkeypatch.setenv("AGENT_CONFIG_PATH", str(tmp_path / "missing.toml"))
    assert main(["chat", "你好"]) == 1


def test_cli_add_file(tmp_path):
    doc = tmp_path / "note.txt"
    doc.write_text("这是一个通过文件路径添加的文档。" * 5, encoding="utf-8")

    assert main(["add", str(doc)]) == 0
    assert main(["stats"]) == 0
