# api

FastAPI 业务应用。

## 运行

在仓库根目录执行：

```bash
# 通过项目入口启动
uv run --directory apps/api api

# 或开发模式（--reload 热重载）
uv run --directory apps/api uvicorn api:app --reload --port 8000

# 访问
#   http://127.0.0.1:8000/         -> {"message": "Hello, monorepo!"}
#   http://127.0.0.1:8000/health   -> {"status": "ok"}
#   http://127.0.0.1:8000/docs     -> Swagger UI
```

> 项目为 src 布局的可安装包（与 `apps/agent`、`packages/*` 形态一致），
> 依赖（含 workspace 内的 `common-utils`）由根虚拟环境统一提供。
