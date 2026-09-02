# ai-test — Python Monorepo (uv workspace)

基于 [uv](https://docs.astral.sh/uv/) workspace 的 Python 单仓多包模板。
**一份 `uv.lock`、一个 `.venv`** 统一管理所有成员；库与应用采用不同的打包策略。

```
.
├── pyproject.toml          # 虚拟 workspace 根（自身不可安装）+ 工具链配置
├── uv.lock                 # 全仓库统一锁文件（需提交）
├── packages/               # ① 可安装 / 可发布的库
│   └── common-utils/       #    src 布局：src/common_utils/，含 build-system
└── apps/                   # ② 业务应用（不发布，源码运行，package = false）
    ├── api/                #    FastAPI 服务
    └── worker/             #    脚本 / 批处理服务
```

## 两类成员的区别

| | `packages/*` 库 | `apps/*` 应用 |
| --- | --- | --- |
| 布局 | **src 布局**（`src/<pkg>/`） | 扁平（`main.py` 直接在应用目录） |
| `[build-system]` | ✅ 有（`uv_build`） | ❌ 无 |
| `[tool.uv] package` | 默认 `true`（可构建） | `false`（不安装、不发布） |
| 用途 | 开源组件 / 内部公共包，可 `uv build` / `uv publish` | FastAPI、脚本服务，仅内部运行 |
| 被引用 | 作为依赖被应用安装（workspace 内**可编辑链接**） | 不被其它包依赖 |

## 环境准备

```bash
# 安装 uv（macOS）
brew install uv

# 在仓库根目录安装全部依赖（含 dev 工具组），生成 .venv 与 uv.lock
uv sync --dev
```

## 常用命令（均在仓库根目录执行）

```bash
# 跑全部测试（pytest 根配置已把 testpaths 指向 packages/ 与 apps/）
uv run pytest

# 代码检查 / 自动修复
uv run ruff check .
uv run ruff check --fix .

# 运行 FastAPI 应用（--directory 切到应用目录，使其源码可被 import）
uv run --directory apps/api uvicorn main:app --reload --port 8000

# 运行脚本服务
uv run --directory apps/worker python main.py
```

## 新增一个成员

```bash
# 新增库（可发布）：建目录 packages/<lib>/，写 pyproject.toml（带 build-system）
#   代码放 packages/<lib>/src/<import_name>/
# 新增应用（不发布）：建目录 apps/<app>/，写 pyproject.toml（末尾加 [tool.uv] package=false）

# 若新库需要被其它成员依赖，在根 pyproject.toml 的 [tool.uv.sources] 里登记：
#   <lib-dist-name> = { workspace = true }
# 然后在应用的 dependencies 里写上 <lib-dist-name> 即可。

uv sync        # 重新解析、安装新成员
```

## 构建 / 发布库

```bash
uv build packages/common-utils     # 产出 dist/*.whl 与 *.tar.gz
uv publish packages/common-utils   # 发布到配置的包索引（PyPI / 私有源）
```
