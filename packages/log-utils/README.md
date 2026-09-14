# log-utils

内部日志工具库（**src 布局**，可构建 / 可发布），基于 Python 标准库 `logging` 统一封装。

- 分发名（distribution）：`log-utils`
- 导入名（import）：`log_utils`（刻意避开标准库名 `logging`，防止遮蔽）
- 源码：[`src/log_utils/`](src/log_utils)

## 使用方式

```python
from log_utils import get_logger

# 默认输出到 stderr
logger = get_logger(__name__)
logger.info("服务启动")
# 2026-09-12 10:00:00 | INFO     | my_app | 服务启动

# 传入 log_file 可同时写入文件（父目录自动创建，UTF-8 编码）
file_logger = get_logger(__name__, log_file="logs/app.log")
```

## 在其它成员中使用

业务应用在自己的 `pyproject.toml` 依赖里写上 `log-utils` 即可，
workspace 会自动以**可编辑模式**链到本目录源码：

```toml
dependencies = ["log-utils"]
```

## 构建发布

```bash
uv build packages/log-utils           # 产出 dist/*.whl 与 *.tar.gz
uv publish packages/log-utils         # 发布到配置的包索引
```
