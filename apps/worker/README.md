# worker

脚本 / 批处理服务。适合定时任务、数据处理、CLI 工具。

## 运行

在仓库根目录执行：

```bash
uv run --directory apps/worker worker
# 输出：Hello, worker!
```

> 项目为 src 布局的可安装包（与 `apps/agent`、`packages/*` 形态一致），
> 依赖（含 workspace 内的 `common-utils`）由根虚拟环境统一提供。
