"""配置加载测试：TOML 解析、默认值、环境变量覆盖、缺文件 / 缺项报错。"""

import pytest
from agent.config import load_config

_CONFIG_BODY = """
[llm]
base_url = "https://ark.example.com/api/plan/v3"
api_key = "ark-file-key"
model = "doubao-seed-2.0-mini"
temperature = 0.3
stream = false
max_tokens = 1024
system_prompt = "你是测试助手。"
"""


@pytest.fixture
def config_file(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(_CONFIG_BODY, encoding="utf-8")
    return path


def test_load_config_from_file(config_file):
    config = load_config(config_file)
    assert config.base_url == "https://ark.example.com/api/plan/v3"
    assert config.api_key == "ark-file-key"
    assert config.model == "doubao-seed-2.0-mini"
    assert config.temperature == 0.3
    assert config.stream is False
    assert config.max_tokens == 1024
    assert config.system_prompt == "你是测试助手。"


def test_load_config_defaults(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(
        '[llm]\nbase_url = "https://ark.example.com/v3"\n'
        'api_key = "ark-x"\nmodel = "doubao"\n',
        encoding="utf-8",
    )
    config = load_config(path)
    assert config.temperature == 0.7
    assert config.stream is True
    assert config.max_tokens is None
    assert config.system_prompt is None


def test_api_key_env_override(config_file, monkeypatch):
    monkeypatch.setenv("ARK_API_KEY", "ark-env-key")
    assert load_config(config_file).api_key == "ark-env-key"


def test_env_path_resolution(config_file, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_PATH", str(config_file))
    assert load_config().model == "doubao-seed-2.0-mini"


def test_missing_config_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nope.toml")


def test_missing_required_field_raises(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('[llm]\napi_key = "ark-x"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="base_url"):
        load_config(path)


def test_missing_api_key_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("ARK_API_KEY", raising=False)
    path = tmp_path / "config.toml"
    path.write_text(
        '[llm]\nbase_url = "https://ark.example.com/v3"\nmodel = "doubao"\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="api_key"):
        load_config(path)
