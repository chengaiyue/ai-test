import logging

from log_utils import __version__, get_logger


def test_get_logger_returns_named_logger():
    logger = get_logger("test_named")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_named"


def test_get_logger_does_not_duplicate_handlers():
    logger1 = get_logger("test_dup")
    logger2 = get_logger("test_dup")
    assert logger1 is logger2
    assert len(logger2.handlers) == 1


def test_get_logger_disables_propagation():
    logger = get_logger("test_propagate")
    assert logger.propagate is False


def test_get_logger_writes_to_file(tmp_path):
    log_file = tmp_path / "logs" / "app.log"
    logger = get_logger("test_file", log_file=log_file)
    logger.info("文件日志内容")
    for handler in logger.handlers:
        handler.flush()

    assert log_file.exists()
    assert "文件日志内容" in log_file.read_text(encoding="utf-8")


def test_get_logger_does_not_duplicate_file_handler(tmp_path):
    log_file = tmp_path / "app.log"
    get_logger("test_file_dup", log_file=log_file)
    logger = get_logger("test_file_dup", log_file=log_file)

    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) == 1


def test_get_logger_keeps_stream_handler_alongside_file(tmp_path):
    logger = get_logger("test_both", log_file=tmp_path / "app.log")

    assert any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        for h in logger.handlers
    )
    assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)


def test_version_is_string():
    assert isinstance(__version__, str)
