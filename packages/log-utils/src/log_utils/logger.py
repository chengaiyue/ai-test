"""日志工具：基于标准库 logging 的统一封装。"""

import logging
import sys
from pathlib import Path

_DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


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


def get_logger(
    name: str | None = None,
    level: int = logging.INFO,
    log_file: str | Path | None = None,
) -> logging.Logger:
    """获取统一配置的 logger。

    - 默认输出到 stderr，格式为「时间 | 级别 | 名称 | 消息」。
    - 传入 ``log_file`` 时额外输出到该文件，父目录不存在会自动创建，编码 UTF-8。
    - 同类型 handler（含同路径文件 handler）重复调用不会叠加。
    - 关闭向 root logger 的传播，避免业务应用侧重复打印。

    Args:
        name: logger 名称，通常传 ``__name__``；为 None 时返回 root logger。
        level: 日志级别，默认 ``logging.INFO``。
        log_file: 日志文件路径；为 None 时不写文件。
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if not _has_handler(logger, logging.StreamHandler):
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT, _DEFAULT_DATE_FORMAT))
        logger.addHandler(stream_handler)

    if log_file is not None:
        log_path = Path(log_file).resolve()
        for handler in logger.handlers:
            if (
                isinstance(handler, logging.FileHandler)
                and Path(handler.baseFilename).resolve() == log_path
            ):
                break
        else:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT, _DEFAULT_DATE_FORMAT))
            logger.addHandler(file_handler)

    return logger
