"""FastAPI 示例应用入口。

运行（仓库根目录）：
    uv run --directory apps/api api
或开发模式：
    uv run --directory apps/api uvicorn api:app --reload
"""

import uvicorn
from fastapi import FastAPI

from common_utils import greet

app = FastAPI(title="api")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": greet("monorepo")}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    """服务入口。"""
    uvicorn.run(app, host="127.0.0.1", port=8000)
