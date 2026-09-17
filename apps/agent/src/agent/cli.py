"""agent 命令行：向量库的添加 / 查询 / 统计，以及火山方舟大模型对话。

用法（仓库根目录）：
    uv run agent add README.md [more.txt ...] [--title 标题]
    uv run agent add --text "直接传入一段文本" [--source 来源]
    uv run agent search "查询内容" [-k 5]
    uv run agent chat "问大模型一个问题" [--system 系统提示词] [--no-stream]
    uv run agent stats
    uv run agent hello
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from log_utils import get_logger

from agent.vectorstore import VectorStore
from agent.vectorstore.document import make_document
from agent.vectorstore.embeddings import embedder_name

logger = get_logger(__name__)


def _load_documents(args: argparse.Namespace):
    """从文件和 --text 构造文档列表。"""
    documents = []
    for path in args.paths:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.error("读取文件失败 %s: %s", path, exc)
            raise SystemExit(1) from exc
        documents.append(make_document(content, title=args.title, source=str(path)))
    if args.text:
        for text in args.text:
            documents.append(make_document(text, title=args.title, source=args.source))
    if not documents:
        raise SystemExit("没有可添加的内容：请给出文件路径或 --text")
    return documents


def _cmd_add(args: argparse.Namespace) -> int:
    store = VectorStore()
    result = store.add_documents(_load_documents(args))
    for doc_hash in result.added_hashes:
        logger.info("新文档已入库：%s", doc_hash[:12])
    for doc_hash in result.duplicate_hashes:
        logger.info("重复文档，跳过：%s", doc_hash[:12])
    print(
        f"新增文档 {result.added_count} 篇（切片 {result.chunks_added} 个），"
        f"跳过重复文档 {result.duplicate_count} 篇"
    )
    return 0


def _cmd_search(args: argparse.Namespace) -> int:
    store = VectorStore()
    hits = store.search(args.query, k=args.k)
    if not hits:
        print("未检索到任何切片（向量库可能为空）。")
        return 0
    print(f"查询：{args.query}    嵌入器：{embedder_name(store.embeddings)}\n")
    for index, hit in enumerate(hits, start=1):
        source = hit.metadata.get("source") or hit.metadata.get("doc_hash", "?")[:12]
        print(f"[{index}] 分数 {hit.score:.4f} | 来源 {source}")
        print(f"    {hit.content.strip()[:200]}")
        print()
    return 0


def _cmd_chat(args: argparse.Namespace) -> int:
    """调用火山方舟大模型，默认逐 token 流式打印回复。"""
    # 延迟导入：向量库类命令不需要大模型配置 / openai SDK
    from agent.config import load_config
    from agent.llm.agent import build_chat_agent, invoke_agent, stream_agent

    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as exc:
        logger.error("%s", exc)
        return 1

    agent = build_chat_agent(config=config)
    system_prompt = args.system if args.system is not None else config.system_prompt
    streaming = config.stream if args.stream is None else args.stream

    try:
        if streaming:
            for token in stream_agent(agent, args.prompt, system_prompt=system_prompt):
                print(token, end="", flush=True)
            print()
        else:
            print(invoke_agent(agent, args.prompt, system_prompt=system_prompt))
    except Exception as exc:  # 网络 / 鉴权 / 模型错误统一收口，避免甩出整段堆栈
        logger.error("调用火山方舟大模型失败：%s", exc)
        return 1
    return 0


def _cmd_stats(_args: argparse.Namespace) -> int:
    store = VectorStore()
    stats = store.stats()
    print(
        f"集合 {store.collection_name}（{store.path}）："
        f"文档 {stats['documents']} 篇，切片 {stats['chunks']} 个"
    )
    return 0


def _cmd_hello(_args: argparse.Namespace) -> int:
    print("Hello from agent!")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent", description="向量数据库（切片 / 查重 / 相似度查询）与火山方舟大模型对话"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add = subparsers.add_parser("add", help="添加文档（文件或 --text），重复文档自动跳过")
    add.add_argument("paths", nargs="*", type=Path, help="文本文件路径")
    add.add_argument("--text", action="append", help="直接传入文本，可重复使用")
    add.add_argument("--title", help="文档标题（可选）")
    add.add_argument("--source", help="--text 文本的来源标识（可选）")
    add.set_defaults(handler=_cmd_add)

    search = subparsers.add_parser("search", help="语义相似度查询")
    search.add_argument("query", help="查询内容")
    search.add_argument("-k", type=int, default=5, help="返回切片数量（默认 5）")
    search.set_defaults(handler=_cmd_search)

    chat = subparsers.add_parser("chat", help="调用火山引擎方舟大模型（默认流式输出）")
    chat.add_argument("prompt", help="问题 / 提示词")
    chat.add_argument("--system", help="系统提示词（覆盖配置文件中的 system_prompt）")
    chat.add_argument(
        "--stream",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="是否流式输出（默认取配置文件 stream，命令行用 --stream / --no-stream 覆盖）",
    )
    chat.set_defaults(handler=_cmd_chat)

    stats = subparsers.add_parser("stats", help="查看文档 / 切片数量")
    stats.set_defaults(handler=_cmd_stats)

    hello = subparsers.add_parser("hello", help="打印欢迎语")
    hello.set_defaults(handler=_cmd_hello)
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI 入口。"""
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    return args.handler(args)
