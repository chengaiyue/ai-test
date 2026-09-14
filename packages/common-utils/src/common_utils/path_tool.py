import os


def get_project_root():
    """从当前文件向上查找 monorepo 根目录（包含 apps 目录的一级）。"""
    current = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.isdir(os.path.join(current, "apps")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            raise FileNotFoundError("无法定位项目根目录：上级目录中未找到 apps 目录")
        current = parent


def get_abs_path(path):
    current_path = get_project_root()
    return os.path.join(current_path, path)
