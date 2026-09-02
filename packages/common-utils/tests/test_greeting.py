from common_utils import __version__, greet


def test_greet():
    assert greet("monorepo") == "Hello, monorepo!"


def test_version_is_string():
    assert isinstance(__version__, str)
