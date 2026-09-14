import logging

from log_utils import __version__, get_logger


def test_get_logger_returns_named_logger():
    logger = get_logger("test_named")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_named"


def test_get_logger_does_not_duplicate_handlers():
    logger1 = get_logger("test_dup", log_file=None)
    logger2 = get_logger("test_dup", log_file=None)
    assert logger1 is logger2
    assert len(logger2.handlers) == 1


def test_get_logger_disables_propagation():
    logger = get_logger("test_propagate", log_file=None)
    assert logger.propagate is False


def test_get_logger_defaults_to_log_dir_at_project_root(tmp_path, monkeypatch):
    # tmp_path 作为最顶层项目目录（含 pyproject.toml），在其下子目录中运行
    (tmp_path / "pyproject.toml").touch()
    workdir = tmp_path / "apps" / "svc"
    workdir.mkdir(parents=True)
    monkeypatch.chdir(workdir)

    log_file = tmp_path / "log" / "test_default.log"
    logger = get_logger("test_default")
    logger.info("默认文件日志")
    for handler in logger.handlers:
        handler.flush()

    assert log_file.exists()
    assert "默认文件日志" in log_file.read_text(encoding="utf-8")


def test_get_logger_prefers_workspace_root(tmp_path, monkeypatch):
    # workspace 根含 uv.lock；即使内层 app 目录也有 pyproject.toml，仍应取最顶层
    (tmp_path / "uv.lock").touch()
    app_dir = tmp_path / "apps" / "svc"
    app_dir.mkdir(parents=True)
    (app_dir / "pyproject.toml").touch()
    monkeypatch.chdir(app_dir)

    get_logger("test_ws_root").info("workspace 根日志")
    for handler in logging.getLogger("test_ws_root").handlers:
        handler.flush()

    assert (tmp_path / "log" / "test_ws_root.log").exists()
    assert not (app_dir / "log").exists()


def test_get_logger_none_disables_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    logger = get_logger("test_no_file", log_file=None)

    assert not [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert not (tmp_path / "log").exists()


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
