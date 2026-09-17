"""大模型配置：从 TOML 配置文件读取火山引擎方舟（Agent Plan）连接信息。

配置查找顺序：
    1. 显式传入的路径；
    2. 环境变量 ``AGENT_CONFIG_PATH``；
    3. ``<仓库根>/apps/agent/config.toml``；
    4. 当前工作目录下的 ``config.toml``。

配置文件示例见 ``apps/agent/config.example.toml``。``api_key`` 还可用环境变量
``ARK_API_KEY`` 覆盖，方便在不落盘密钥的环境中运行。
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_ENV_VAR = "AGENT_CONFIG_PATH"
API_KEY_ENV_VAR = "ARK_API_KEY"

_CONFIG_SECTION = "llm"
_REQUIRED_FIELDS = ("base_url", "model")


@dataclass(frozen=True)
class LLMConfig:
    """火山方舟大模型连接与生成参数。"""

    base_url: str
    api_key: str
    model: str
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = True
    system_prompt: str | None = None


def candidate_config_paths() -> list[Path]:
    """按查找顺序返回候选配置文件路径（不保证存在）。"""
    candidates: list[Path] = []
    env_path = os.environ.get(CONFIG_ENV_VAR)
    if env_path:
        candidates.append(Path(env_path))
    # 延迟导入：脱离 monorepo（如临时目录）时不依赖其目录结构
    try:
        from common_utils.path_tool import get_abs_path

        candidates.append(Path(get_abs_path("apps/agent/config.toml")))
    except (ImportError, FileNotFoundError):
        pass
    candidates.append(Path.cwd() / "config.toml")
    return candidates


def default_config_path() -> Path | None:
    """返回配置文件路径。

    设置了 ``AGENT_CONFIG_PATH`` 时以它为准（即使文件不存在，交由 ``load_config``
    报错而不是静默回退）；否则返回第一个存在的候选路径，都没有则返回 None。
    """
    env_path = os.environ.get(CONFIG_ENV_VAR)
    if env_path:
        return Path(env_path)
    return next((path for path in candidate_config_paths() if path.is_file()), None)


def load_config(path: str | Path | None = None) -> LLMConfig:
    """加载并校验大模型配置。

    Raises:
        FileNotFoundError: 找不到配置文件。
        ValueError: 配置缺少必填项，或密钥为空。
    """
    config_path = Path(path) if path is not None else default_config_path()
    if config_path is None or not config_path.is_file():
        searched = "\n  ".join(str(p) for p in candidate_config_paths())
        raise FileNotFoundError(
            "找不到大模型配置文件，请复制 apps/agent/config.example.toml 为 "
            f"config.toml 并填写密钥（或设置 {CONFIG_ENV_VAR}）。已查找：\n  {searched}"
        )

    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get(_CONFIG_SECTION, {})

    missing = [name for name in _REQUIRED_FIELDS if not section.get(name)]
    if missing:
        fields = ", ".join(missing)
        raise ValueError(
            f"配置文件 {config_path} 的 [{_CONFIG_SECTION}] 缺少必填项：{fields}"
        )

    # 环境变量优先，避免在 CI 等场景把密钥写进文件
    api_key = os.environ.get(API_KEY_ENV_VAR) or section.get("api_key", "")
    if not api_key:
        raise ValueError(
            f"配置文件 {config_path} 未配置 api_key，也未设置 {API_KEY_ENV_VAR} 环境变量"
        )

    return LLMConfig(
        base_url=section["base_url"],
        api_key=api_key,
        model=section["model"],
        temperature=float(section.get("temperature", 0.7)),
        max_tokens=section.get("max_tokens"),
        stream=bool(section.get("stream", True)),
        system_prompt=section.get("system_prompt"),
    )
