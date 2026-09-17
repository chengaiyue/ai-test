"""CLI 冒烟测试：add（含查重）→ search → stats。"""

import pytest
from agent.cli import main


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


def test_cli_add_file(tmp_path):
    doc = tmp_path / "note.txt"
    doc.write_text("这是一个通过文件路径添加的文档。" * 5, encoding="utf-8")

    assert main(["add", str(doc)]) == 0
    assert main(["stats"]) == 0
