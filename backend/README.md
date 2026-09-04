# NexusAI Backend

FastAPI 后端，负责认证、知识库、文档处理、RAG、LangGraph 工作流、长期记忆、Skills、Tools 和 MCP 管理。

## 运行环境

- Python 3.12
- PostgreSQL 16
- Redis 7
- ChromaDB 0.5

Python 依赖见 `requirements.txt`。

## 目录结构

```text
backend/
├── alembic/                 # Alembic 数据库迁移
├── app/
│   ├── agent/
│   │   ├── nodes/           # LangGraph 节点
│   │   ├── skills/          # Skills 注册与实现
│   │   ├── tools/           # 内置 Tools 与审批规则
│   │   ├── graph.py         # 主图构建
│   │   └── checkpoint.py    # PostgreSQL/Memory Checkpointer
│   ├── api/                 # FastAPI 路由
│   ├── core/                # 配置、数据库、JWT、日志、限流
│   ├── mcp/                 # MCP Client 与 stdio Server
│   ├── memory/              # 长期记忆与 Profile Slots
│   ├── models/              # SQLAlchemy 模型
│   ├── rag/                 # 文档解析、分块、检索和重排
│   ├── schemas/             # Pydantic 请求/响应模型
│   ├── services/            # 业务服务
│   └── tasks/               # Celery 任务
├── scripts/                 # 本地调试和端到端测试脚本
├── .env.example
├── alembic.ini
├── Dockerfile
├── main.py
└── requirements.txt
```

## 环境变量

应用从 `../.env` 和当前目录 `.env` 读取配置。可以从项目根目录模板开始：

```powershell
Copy-Item ..\.env.example ..\.env
```

主要变量：

| 变量 | 用途 |
|---|---|
| `APP_HOST` / `APP_PORT` | FastAPI 监听地址和端口 |
| `POSTGRES_*` | PostgreSQL 连接信息 |
| `REDIS_*` | Redis 连接信息 |
| `CELERY_*` | Celery Broker 与结果后端 |
| `JWT_SECRET_KEY` | JWT 签名密钥 |
| `DEEPSEEK_*` | 对话模型配置 |
| `DASHSCOPE_API_KEY` | Embedding 与 Reranker 凭证 |
| `TAVILY_API_KEY` | Web 搜索凭证，可选 |
| `CHROMA_HOST/PORT` | ChromaDB HTTP 模式 |
| `CHROMA_PERSIST_PATH` | 非空时使用嵌入式 ChromaDB |

不要提交包含真实凭证的 `.env`。

## 本地启动

### 1. 创建环境并安装依赖

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. 执行数据库迁移

```powershell
alembic upgrade head
```

仓库已经包含迁移脚本，本地启动时不需要重新执行 `alembic revision`。

### 3. 启动 API

与前端 Vite 代理配套的开发端口为 `8002`：

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

访问：

- Swagger：http://localhost:8002/docs
- ReDoc：http://localhost:8002/redoc
- 健康检查：http://localhost:8002/api/v1/health

### 4. 启动 Celery Worker

另开一个 PowerShell 窗口：

```powershell
.\.venv\Scripts\Activate.ps1
celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=4
```

## API 模块

所有业务接口使用 `/api/v1` 前缀。

| 模块 | 主要能力 |
|---|---|
| `auth` | 注册、登录、当前用户 |
| `knowledge_base` | 知识库 CRUD |
| `document` | 上传、列表、预览、重新处理、检索 |
| `task` | 异步任务状态 |
| `chat` | 会话、同步消息、SSE 消息、审批恢复、取消 |
| `memory` | 长期事实查询与删除 |
| `memory_profile` | Profile Slots 与候选确认 |
| `skill` | Skills 列表与测试执行 |
| `mcp` | MCP Server 配置、连接测试和工具发现 |

具体请求和响应结构以 Swagger 为准。

## Agent 工作流

主图定义在 `app/agent/graph.py`：

```text
START → context_prep → supervisor
                         ├─ rag_agent ───────────────┐
                         ├─ tool_agent ──────────────┤
                         ├─ business_context_agent ──┘
                         ├─ synthesis_agent → END
                         └─ FINISH → END
```

Supervisor 通过 `MAX_ITERATIONS = 5` 限制循环次数。外部 MCP Tool 默认在执行前触发 LangGraph `interrupt()`；用户批准后通过 `Command(resume=...)` 恢复。

## 文档处理流程

文档上传后由 Celery 执行：

```text
保存文件 → 解析文本 → 可选结构修订 → 分块 → Embedding → 写入 ChromaDB
```

支持 PDF、DOCX、PPTX、Markdown 和常见文本格式。未配置通义凭证时，Embedding 会按配置决定是否回退到 Mock 实现。

## 测试脚本

`scripts/` 中保留的是本地调试与端到端链路检查脚本。需要登录的脚本从以下环境变量读取测试账号：

```dotenv
NEXUS_TEST_USERNAME=
NEXUS_TEST_PASSWORD=
```

这些变量只用于本地测试脚本，不应填写真实生产账号。

## 运行边界

- `get_weather` 当前是 Mock Tool。
- Tavily 未配置时，`web_search` 不可用。
- PostgreSQL Checkpointer 初始化失败时会退回 `MemorySaver`。
- MCP Client 支持 stdio 与 SSE；内置 MCP Server 使用 stdio。
