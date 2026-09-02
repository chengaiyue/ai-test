"""脚本服务示例：可被命令行 / 定时任务直接调用。

运行（仓库根目录）：
    uv run --directory apps/worker python main.py
"""

from common_utils import greet


def main() -> None:
    """脚本入口。"""
    print(greet("worker"))


if __name__ == "__main__":
    main()
