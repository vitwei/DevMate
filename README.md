# DevMate - 智能编程助手

DevMate 是一个 AI 驱动的编程助手，基于 LangChain 框架构建，帮助开发者生成和修改代码库。

## 功能特性

- 🤖 **智能 Agent**: 基于 LangChain 的智能代理，自主决策工具调用
- 🌐 **MCP 网络搜索**: 使用 Model Context Protocol (MCP) 集成 Tavily 搜索服务
- 📚 **RAG 文档检索**: 本地知识库检索增强生成
- 🛠️ **Agent Skills**: 技能学习与复用机制
- 🐳 **Docker 容器化**: 一键部署
- 📊 **可观测性**: LangSmith 集成，追踪 Agent 执行过程

## 技术栈

- **Python 3.13
- **LangChain >= 1.2.10
- **MCP (Model Context Protocol)**
- **FAISS** (向量数据库)
- **Tavily** (网络搜索)
- **uv** (依赖管理)
- **FastAPI / Uvicorn** (Web 服务)

## 项目结构

```
DevMate/
├── src/
│   ├── agent/              # Agent 核心模块
│   │   ├── agent.py      # Agent 实现
│   │   ├── prompts/    # 提示词管理
│   │   ├── skills/     # Skills 系统
│   │   └── tool/       # 工具管理
│   ├── mcp_server/      # MCP Server
│   │   └── server.py # 网络搜索服务
│   ├── rag/             # RAG 模块
│   │   ├── embedding.py
│   │   ├── ingest.py
│   │   └── retriever.py
│   ├── web/             # Web UI
│   ├── cli.py           # CLI 入口
│   ├── config.py         # 配置管理
│   └── logging_config.py
├── docker/               # Docker 配置
├── .knowledge/           # 知识库
│   ├── docs/           # 文档目录
│   └── vector_db/      # 向量数据库
├── .skills/              # Skills 目录
├── workspace/           # 工作空间
└── config.toml        # 配置文件
```

## 快速开始

### 前置要求

- Python 3.13
- uv (依赖管理工具)
- Docker (可选，用于容器化运行)

### 安装

1. 克隆仓库：
```bash
git clone <repository-url>
cd DevMate
```

2. 使用 uv 安装依赖：
```bash
uv sync
```

### 配置

创建 `config.toml` 配置文件（参考示例）：

```toml
[model]
ai_base_url = "https://api.openai.com/v1"
api_key = "your-api-key"
model_name = "gpt-4o"
embedding_model_name = "text-embedding-3-small"

[search]
tavily_api_key = "your-tavily-api-key"

[langsmith]
langchain_tracing_v2 = true
langchain_api_key = "your-langsmith-api-key"
langchain_project = "DevMate"

[skills]
skills_dir = ".skills"

[server]
host = "0.0.0.0"
port = 5003
debug = false

[rag]
vector_store_path = ".knowledge/vector_db"
chunk_size = 1000
chunk_overlap = 200
top_k = 3
kb_dir = ".knowledge/docs"

[file]
work_dir = "workspace"
```

### 使用方法

#### 1. 交互式聊天模式

```bash
uv run devmate chat
```

#### 2. 一次性问答模式

```bash
uv run devmate ask "构建一个待办事项应用的 FastAPI 服务"
```

#### 3. 启动 Web UI

```bash
uv run devmate serve
```

#### 4. 启动 MCP Server

```bash
uv run src.mcp_server.server
```

### Docker 部署

使用 Docker Compose 启动：

```bash
cd docker
docker-compose up -d
```

## 核心功能说明

### MCP 网络搜索

DevMate 使用 MCP 协议通过 Streamable HTTP 连接 Tavily 搜索服务，为 Agent 提供实时网络搜索能力。

### RAG 文档检索

将本地文档（Markdown/Text）索引到 FAISS 向量数据库中，Agent 可通过 `search_knowledge_base` 工具检索相关文档。

### Agent Skills

Agent 可以学习和复用常见任务模式，Skills 存储在 `.skills` 目录中。

## 开发指南

### 代码规范

- 严格遵循 [PEP 8](https://peps.python.org/pep-0008/) 编码规范
- 使用 `logging` 模块进行日志输出，禁止使用 `print()`
- 所有配置通过 `config.toml` 管理

### 可观测性

项目集成了 LangSmith，可通过 LangSmith 控制台查看完整的 Agent 执行 Trace。

## 许可证

MIT License
