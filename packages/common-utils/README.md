# common-utils

内部公共工具库（**src 布局**，可构建 / 可发布）。

- 分发名（distribution）：`common-utils`
- 导入名（import）：`common_utils`
- 源码：[`src/common_utils/`](src/common_utils)

## 在其它成员中使用

业务应用在自己的 `pyproject.toml` 依赖里写上 `common-utils` 即可，
workspace 会自动以**可编辑模式**链到本目录源码：

```toml
dependencies = ["common-utils"]
```

## 构建发布

```bash
uv build packages/common-utils           # 产出 dist/*.whl 与 *.tar.gz
uv publish packages/common-utils         # 发布到配置的包索引
```
