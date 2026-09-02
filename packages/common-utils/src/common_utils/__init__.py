"""common_utils —— 内部公共工具库。

库代码统一放在 ``src/common_utils`` 下（src 布局）：
导入时走的是“已安装”的包，而不是仓库根目录，能在开发期就暴露打包配置问题。
"""

from importlib.metadata import PackageNotFoundError, version

from common_utils.greeting import greet

__all__ = ["greet", "__version__"]

try:
    __version__ = version("common-utils")
except PackageNotFoundError:  # 未安装（如直接读源码）时的兜底
    __version__ = "0.0.0"
