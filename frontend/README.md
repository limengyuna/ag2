# NexusAI Frontend

基于 Vue 3、TypeScript、Vite、Pinia 和 Tailwind CSS 的单页应用。

## 技术栈

| 类别 | 技术 |
|---|---|
| 框架 | Vue 3.5、Composition API |
| 构建 | Vite 5、TypeScript 5.6 |
| 状态管理 | Pinia 2 |
| 路由 | Vue Router 4 |
| 请求 | Axios、Fetch、ReadableStream |
| 样式 | Tailwind CSS 3 |

## 本地启动

安装依赖：

```powershell
npm install
```

启动开发服务器：

```powershell
npm run dev
```

访问 http://localhost:5173。

Vite 会把 `/api` 请求代理到 `http://localhost:8002`，因此需要先在 `8002` 端口启动后端。

## 生产构建

```powershell
npm run build
```

构建产物位于 `dist/`。Docker 镜像使用 Nginx 托管静态文件，并将 `/api` 请求转发到后端容器。

## 页面路由

| 路由 | 页面 | 功能 |
|---|---|---|
| `/login` | LoginView | 登录与注册 |
| `/chat` | ChatView | 流式对话、执行过程、审批与重新生成 |
| `/knowledge` | KnowledgeView | 知识库和文档管理 |
| `/memory` | MemoryView | 长期记忆、用户档案和候选项管理 |
| `/skills` | SkillsView | Skills 列表与测试 |
| `/mcp` | MCPView | MCP Server 配置与工具查看 |

除登录页和 404 页面外，其余页面需要 JWT 登录状态。

## 目录结构

```text
frontend/
├── src/
│   ├── api/                 # REST 与 SSE 请求封装
│   ├── components/
│   │   ├── chat/            # 对话与执行过程组件
│   │   ├── knowledge/       # 知识库和文档组件
│   │   ├── mcp/             # MCP 配置组件
│   │   └── memory/          # 记忆管理组件
│   ├── composables/         # 通用组合式函数
│   ├── layouts/             # 应用布局
│   ├── router/              # 路由和登录守卫
│   ├── stores/              # Pinia 状态
│   ├── utils/               # Markdown 等工具
│   ├── views/               # 页面视图
│   ├── App.vue
│   ├── main.ts
│   └── style.css
├── Dockerfile
├── nginx.conf
├── package.json
└── vite.config.ts
```

## 数据流边界

- 普通 REST 请求通过 Axios 实例发送，并自动附带 JWT。
- 流式对话使用 Fetch 读取 SSE，支持主动取消和审批恢复。
- Token 保存在前端本地状态中；不要在日志、截图或提交内容中暴露真实 Token。
- 前端只展示后端返回的执行过程，不直接访问 PostgreSQL、Redis 或 ChromaDB。
