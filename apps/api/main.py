"""FastAPI 示例应用入口。

运行（仓库根目录）：
    uv run --directory apps/api uvicorn main:app --reload
"""

from fastapi import FastAPI

from common_utils import greet

app = FastAPI(title="api-app")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": greet("monorepo")}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
