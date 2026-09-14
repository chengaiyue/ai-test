"""日志工具：基于标准库 logging 的统一封装。"""

import logging
import sys
from pathlib import Path
from typing import Any

_DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_LOG_DIR_NAME = "logs"

# 哨兵：区分「未传 log_file（用默认路径）」与「显式传 None（不写文件）」
_UNSET: Any = object()


def _project_root() -> Path:
    """定位运行程序的最顶层目录。

    从当前工作目录逐级向上查找：
      1. 优先含 ``uv.lock`` 的目录（uv workspace 根，整个仓库的最顶层）；
      2. 否则取最近的含 ``pyproject.toml`` 的目录（普通项目根）；
      3. 都找不到时回退到当前工作目录。
    """
    cwd = Path.cwd()
    fallback: Path | None = None
    for directory in (cwd, *cwd.parents):
        if (directory / "uv.lock").exists():
            return directory
        if fallback is None and (directory / "pyproject.toml").exists():
            fallback = directory
    return fallback or cwd


def _default_log_file(name: str | None) -> Path:
    """默认日志文件：<项目根>/log/<logger 名称或 app>.log。"""
    return _project_root() / _LOG_DIR_NAME / f"{name or 'app'}.log"


class _LazyFileHandler(logging.FileHandler):
    """首次真正写日志时才创建目录、打开文件。

    避免仅因导入包 / 调用 get_logger 就在磁盘上留下空的 log 目录和空文件。
    """

    def __init__(self, filename: str | Path, encoding: str = "utf-8") -> None:
        super().__init__(filename, encoding=encoding, delay=True)

    def emit(self, record: logging.LogRecord) -> None:
        if self.stream is None:
            Path(self.baseFilename).parent.mkdir(parents=True, exist_ok=True)
        super().emit(record)


def _has_handler(logger: logging.Logger, handler_type: type) -> bool:
    """判断 logger 是否已有指定类型的 handler。

    FileHandler 是 StreamHandler 的子类，判断 StreamHandler 时需排除文件类 handler，
    否则文件 handler 会被误判成终端 handler。
    """
    for handler in logger.handlers:
        if isinstance(handler, handler_type):
            if handler_type is logging.StreamHandler and isinstance(handler, logging.FileHandler):
                continue
            return True
    return False


def _has_file_handler(logger: logging.Logger, log_path: Path) -> bool:
    """判断 logger 是否已有指向同一文件的文件 handler。"""
    return any(
        isinstance(handler, logging.FileHandler)
        and Path(handler.baseFilename).resolve() == log_path
        for handler in logger.handlers
    )


def get_logger(
    name: str | None = None,
    level: int = logging.INFO,
    log_file: str | Path | None = _UNSET,
) -> logging.Logger:
    """获取统一配置的 logger。

    - 默认输出到 stderr，格式为「时间 | 级别 | 名称 | 消息」。
    - 默认额外写入日志文件 ``<项目根>/log/<name 或 app>.log``：从当前工作目录
      向上找到的最顶层项目目录（含 ``uv.lock`` / ``pyproject.toml``）下的
      ``log`` 文件夹，父目录不存在会自动创建，编码 UTF-8。
    - 显式传入 ``log_file`` 可自定义路径；显式传 ``None`` 表示不写文件。
    - 同名 logger 由 logging 全局单例管理，重复调用不会重建；
      已有的终端 handler 和指向同一路径的文件 handler 都不会重复添加。
    - 关闭向 root logger 的传播，避免业务应用侧重复打印。

    Args:
        name: logger 名称，通常传 ``__name__``；为 None 时返回 root logger。
        level: 日志级别，默认 ``logging.INFO``。
        log_file: 日志文件路径；默认写入项目最顶层 ``log`` 文件夹；
            传 None 时不写文件。
    """
    if log_file is _UNSET:
        log_file = _default_log_file(name)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if not _has_handler(logger, logging.StreamHandler):
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT, _DEFAULT_DATE_FORMAT))
        logger.addHandler(stream_handler)

    if log_file is not None:
        log_path = Path(log_file).resolve()
        if not _has_file_handler(logger, log_path):
            file_handler = _LazyFileHandler(log_path)
            file_handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT, _DEFAULT_DATE_FORMAT))
            logger.addHandler(file_handler)

    return logger


logger = get_logger()
