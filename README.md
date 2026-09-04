# NexusAI

NexusAI 是一个基于 FastAPI、Vue 3 和 LangGraph 的知识库与多 Agent 协作项目。系统支持文档入库、混合检索、流式对话、长期记忆、工具调用审批，以及 MCP Server 的接入与能力暴露。

## 核心能力

### Supervisor 多 Agent 工作流

当前 LangGraph 主图包含以下节点：

```text
START
  → context_prep
  → supervisor
      ├─ rag_agent ───────────────┐
      ├─ tool_agent ──────────────┤
      ├─ business_context_agent ──┘
      ├─ synthesis_agent → END
      └─ FINISH → END
```

- `context_prep`：注入对话摘要、用户档案、长期记忆和当前时间。
- `supervisor`：生成执行计划并调度其他节点，最多循环 5 次。
- `rag_agent`：执行知识库检索、重排、回答生成和忠实度校验。
- `tool_agent`：调用内置 Tool、Skill 或外部 MCP Tool。
- `business_context_agent`：读取当前用户可访问的业务上下文。
- `synthesis_agent`：合并多步骤结果并生成最终回答。

图状态优先使用 PostgreSQL Checkpointer 持久化；初始化失败时会降级为进程内 `MemorySaver`。

### RAG 检索链路

- 支持 Recursive、Markdown Header 和 Semantic 三种分块策略。
- 主查询执行 Dense + BM25 混合检索，并通过 RRF 融合结果。
- 最多生成两个补充查询，补充查询执行 Dense 检索。
- 使用通义 `gte-rerank-v2` 对候选片段重排。
- 支持 Parent-Child 回溯，命中子片段后使用父级内容补全上下文。
- 回答生成后执行引用范围与忠实度校验。

### Skills 与 Tools

项目注册了 5 个 Skills：

- `travel_planner`
- `data_analyst`
- `email_drafter`
- `document_summarizer`
- `research_assistant`

通用 Tool 注册表包含：

- `calculate`
- `rag_search`
- `get_weather`（本地 Mock 实现）
- `web_search`（需要 Tavily API Key）

业务上下文节点还提供 5 个只读工具，用于查询用户工作区、知识库、文档、当前会话和 MCP Server 信息。外部 MCP Tool 默认需要用户审批后执行；通用 Tool 与 Skills 根据内部安全规则执行。

### 长期记忆

- 同时支持用户全局记忆和知识库范围记忆。
- 每个用户、每个知识库范围最多保留 50 条事实。
- 30 天未访问的事实开始衰减重要性。
- 60 天未访问且重要性低于阈值的事实会被清理。
- 用户档案采用固定 Profile Slots，并提供候选确认流程。

## 技术栈

### 后端

- Python 3.12
- FastAPI、Pydantic、Uvicorn
- SQLAlchemy、Alembic、PostgreSQL 16
- Redis、Celery
- LangGraph 0.3.34、PostgreSQL Checkpointer
- ChromaDB、BM25、RRF、通义 Embedding/Reranker
- MCP Python SDK
- Tavily Search API

### 前端

- Vue 3.5、TypeScript、Vite 5
- Vue Router、Pinia
- Tailwind CSS、Lucide Icons
- Fetch、ReadableStream、SSE

## 项目结构

```text
ag2/
├── backend/
│   ├── alembic/              # 数据库迁移
│   ├── app/
│   │   ├── agent/            # LangGraph、Nodes、Skills、Tools
│   │   ├── api/              # FastAPI 路由
│   │   ├── core/             # 配置、数据库、认证、限流
│   │   ├── mcp/              # MCP Client 与 stdio Server
│   │   ├── memory/           # 长期记忆与用户档案
│   │   ├── models/           # SQLAlchemy 模型
│   │   ├── rag/              # 解析、分块、向量检索、重排
│   │   ├── services/         # 业务服务
│   │   └── tasks/            # Celery 任务
│   ├── scripts/              # 本地调试和端到端测试脚本
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── stores/
│   │   └── views/
│   └── vite.config.ts
├── github-readonly-mcp/      # GitHub 只读 MCP 服务
├── docker-compose.yml
├── nexus.bat                 # Windows 本地启动入口
└── .env.example
```

## Docker 启动

### 1. 准备环境变量

在项目根目录执行：

```powershell
Copy-Item .env.example .env
```

至少填写：

```dotenv
POSTGRES_PASSWORD=
JWT_SECRET_KEY=
DEEPSEEK_API_KEY=
DASHSCOPE_API_KEY=
```

`TAVILY_API_KEY` 为可选项，仅 Web 搜索功能需要。

### 2. 启动服务

```powershell
docker compose up -d --build
```

| 服务 | 地址 |
|---|---|
| 前端 | http://localhost |
| Swagger | http://localhost:8002/docs |
| ChromaDB | http://localhost:8001 |

启动后通过前端注册自己的账号。停止服务：

```powershell
docker compose down
```

## 本地开发

本地开发约定：前端运行在 `5173`，后端运行在 `8002`，Vite 将 `/api` 请求代理到 `http://localhost:8002`。

### 后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

Celery Worker 需要单独启动：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=4
```

### 前端

```powershell
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173。

## 主要页面

| 路由 | 功能 |
|---|---|
| `/chat` | SSE 流式对话、执行过程、工具审批、重新生成 |
| `/knowledge` | 知识库、文档上传、分块预览与重新处理 |
| `/memory` | 长期记忆、用户档案和候选项管理 |
| `/skills` | Skills 列表与测试执行 |
| `/mcp` | 外部 MCP Server 配置、连接测试与工具列表 |

## 配置说明

常用配置位于根目录 `.env` 或 `backend/.env`：

| 变量 | 说明 |
|---|---|
| `POSTGRES_*` | PostgreSQL 连接信息 |
| `REDIS_*` | Redis 连接信息 |
| `JWT_SECRET_KEY` | JWT 签名密钥 |
| `DEEPSEEK_*` | 对话模型配置 |
| `DASHSCOPE_API_KEY` | Embedding 与 Reranker 凭证 |
| `TAVILY_API_KEY` | Web 搜索凭证，可选 |
| `CHROMA_HOST/PORT` | ChromaDB HTTP 模式配置 |
| `CHROMA_PERSIST_PATH` | 设置后切换为嵌入式 ChromaDB |

不要把真实 `.env`、Token、Cookie、上传文件或本地调试数据提交到仓库。

## 当前边界

- `get_weather` 返回确定性的 Mock 数据，不是实时天气服务。
- Tavily 未配置时，Web 搜索会返回配置缺失错误。
- Checkpointer 无法连接 PostgreSQL 时会退回内存存储，进程重启后状态不会保留。
- MCP Client 当前支持 stdio 与 SSE；项目自带的 MCP Server 使用 stdio。
