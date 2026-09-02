# api-app

FastAPI 业务应用（内部服务，**不对外发布**）。

## 运行

在仓库根目录执行：

```bash
# 启动开发服务（--reload 热重载）
uv run --directory apps/api uvicorn main:app --reload --port 8000

# 访问
#   http://127.0.0.1:8000/         -> {"message": "Hello, monorepo!"}
#   http://127.0.0.1:8000/health   -> {"status": "ok"}
#   http://127.0.0.1:8000/docs     -> Swagger UI
```

> `--directory apps/api` 让工作目录切到应用目录，`main.py` 才能被 import；
> 依赖（含 workspace 内的 `common-utils`）由根虚拟环境统一提供。
