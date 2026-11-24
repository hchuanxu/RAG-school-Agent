# 项目说明文档 — 校园多源知识库智能问答助手

> **版本**：v2.0 | **最后更新**：2026-06-26

---

## 目录

1. [项目概述](#1-项目概述)
2. [已实现功能详解](#2-已实现功能详解)
3. [技术架构](#3-技术架构)
4. [核心模块说明](#4-核心模块说明)
5. [开发历程与阶段性成果](#5-开发历程与阶段性成果)
6. [接手项目后的运行方法](#6-接手项目后的运行方法)
7. [已知限制与注意事项](#7-已知限制与注意事项)

---

## 1. 项目概述

本项目是一个面向高校师生的智能问答系统，采用 **LangGraph 多智能体 + RAG 检索增强生成** 架构，能够将校园各类文档（章程、规章制度、通知公告等）自动解析、向量化入库，并通过多智能体协作流程为用户提供准确、可溯源的回答。

**核心特色**：
- 5 个智能体协同工作（意图识别 → 检索 → 溯源 → 回答生成 → 审核）
- 支持本地 Ollama 模型，完全免费离线运行
- SSE 流式输出，逐字显示回答
- 回答附带知识库来源溯源（文件名、页码、所属知识库）
- 上传文档自动生成摘要、重点条例、可提问考点
- 学生端与管理端双端设计

---

## 2. 已实现功能详解

### 2.1 学生端功能

#### 智能聊天对话
- **SSE 流式输出**：回答逐字流式显示，使用 Server-Sent Events 直连后端（绕过 Next.js 代理缓冲）
- **多轮对话记忆**：保留对话上下文，支持追问
- **意图识别**：自动识别问题类型（校园政策、教务、奖学金、校园生活、闲聊、超出范围）
- **回答格式规范**：使用 Markdown 结构（小标题、编号列表、无序列表），层次清晰
- **知识库来源**：回答末尾统一列出所有引用来源（文件名、页码、所属知识库名称）
- **内容审核**：自动过滤敏感内容，审核未通过时重试生成（最多 2 次）

#### 知识库浏览
- 查看校园公开知识库列表（卡片式展示，含文档数量）
- 点击进入知识库查看文档列表
- 查看文档详情：文件名、大小、类型、上传时间、处理状态
- 查看文档智能总结：摘要、重点条例、可提问考点

#### 对话历史管理
- 侧边栏显示历史会话列表（按更新时间排序）
- **会话重命名**：hover 显示编辑按钮，行内编辑，Enter 确认 / Esc 取消
- 删除会话
- 自动加载会话消息历史

#### 个人设置
- 查看和修改个人信息
- 修改密码

### 2.2 管理端功能

#### 仪表盘
- **总对话数**：系统累计会话数
- **知识库数**：已创建的知识库总数
- **用户总数**：注册用户数
- **今日提问数**：当天提问数量（按 QuestionLog.asked_at >= 当天零点统计）
- 管理员右上角头像下拉菜单可"返回智能问答"

#### 知识库管理
- 创建知识库（名称、描述、公开/私有）
- 编辑知识库信息
- 删除知识库
- 查看知识库文档数量（SQL outerjoin 统计）

#### 文档管理
- **上传文档**：支持 PDF、Word (.docx)、TXT、Markdown
  - 异步处理：上传后立即返回（`asyncio.to_thread` 在线程中处理，不阻塞事件循环）
  - 前端轮询：每 5 秒检查处理状态，自动更新
  - 文档解析 → 文本清洗 → 递归切片 → Ollama 向量化 → ChromaDB 入库
- 删除文档（同步删除向量与磁盘文件）
- 重新索引文档
- 批量删除

#### 用户管理
- 查看用户列表
- 禁用/启用用户
- 修改用户角色

#### 数据统计
- **意图分布**：各类型问题占比饼图
- **热门问题**：高频提问统计
- **无效问题分析**：识别无法回答的问题
- **问题趋势**：提问数量趋势图

#### FAQ 管理
- 自动从高频问题生成 FAQ
- 手动创建/编辑/删除 FAQ
- FAQ 分类管理

### 2.3 创新功能

#### 智能文档总结
上传文档后自动触发三个生成器（均在后台异步执行）：
1. **文档摘要**：生成结构化摘要（标题、主要内容、重要规定）
2. **重点条例**：提取文档中的关键条款（标题、内容、来源位置、分类、重要性评分）
3. **可提问考点**：基于文档内容生成问答对（问题、答案、难度、分类、来源位置）

**考点 JSON 解析容错**：LLM 返回的 JSON 可能格式不完整，采用 4 级降级解析策略：
1. 直接 `json.loads`
2. JSON 修复（移除尾逗号、补全截断括号、移除控制字符）
3. `raw_decode` 解析首个完整 JSON 值
4. 逐对象挽救（平衡括号法逐个提取 `{...}`，跳过损坏条目）

#### 热门问题统计
- `QuestionRecorder` 在每次问答时自动记录：问题内容、意图分类、是否有效、用户 ID、会话 ID
- 管理端自动聚合统计高频问题，生成校园 FAQ

---

## 3. 技术架构

### 3.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (Next.js 14)                        │
│  ┌──────────────┐    ┌──────────────┐                          │
│  │   学生端      │    │   管理端      │                          │
│  │ 聊天/知识库/历史│   │仪表盘/文档管理│                          │
│  └──────┬───────┘    └──────┬───────┘                          │
└─────────┼───────────────────┼──────────────────────────────────┘
          │  REST (axios)     │  SSE (fetch 直连 :8000)
          ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    后端 (FastAPI + Uvicorn)                      │
│  ┌─────────┐ ┌──────────────┐ ┌─────────────────────────────┐  │
│  │  API    │ │   Services   │ │    LangGraph 多智能体         │  │
│  │ 11 路由  │ │ 业务逻辑层   │ │ 意图→检索→溯源→回答→审核      │  │
│  └────┬────┘ └──────┬───────┘ └─────────────────┬─────────────┘  │
│       │             │                           │                 │
│       ▼             ▼                           ▼                 │
│  ┌─────────┐ ┌──────────────┐ ┌─────────────────────────────┐  │
│  │ SQLite  │ │  RAG 系统    │ │         ChromaDB            │  │
│  │ 业务数据 │ │ 解析/切片/   │ │ 向量数据库(持久化存储)      │  │
│  │         │ │ 向量化/检索  │ │ Ollama 嵌入(nomic-embed)    │  │
│  └─────────┘ └──────────────┘ └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LLM 提供商 (Ollama)                          │
│  ┌──────────────┐    ┌──────────────┐                          │
│  │ qwen2.5:7b   │    │nomic-embed-   │                          │
│  │ 对话/摘要/   │    │text           │                          │
│  │ 条例/考点    │    │ 文档/查询嵌入  │                          │
│  └──────────────┘    └──────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **后端框架** | FastAPI | 0.115.6 | 异步 Web 框架 |
| **ORM** | SQLAlchemy | 2.0.36 | 异步 ORM (Mapped/mapped_column) |
| **验证** | Pydantic | 2.10.4 | 数据验证与设置 |
| **多智能体** | LangGraph | 0.2.60 | StateGraph 工作流 |
| **LLM 编排** | LangChain | 0.3.14 | LLM 调用 |
| **向量数据库** | ChromaDB | 0.5.23 | 持久化向量存储 |
| **LLM** | Ollama | - | 本地 qwen2.5:7b + nomic-embed-text |
| **前端框架** | Next.js | 14.2.20 | App Router |
| **状态管理** | Zustand | 4.5.5 | 轻量状态管理 |
| **样式** | TailwindCSS | 3.4.17 | 原子化 CSS |
| **图表** | Recharts | 2.15.0 | 数据可视化 |
| **认证** | JWT (python-jose) + bcrypt | - | 令牌认证 + 密码哈希 |

### 3.3 LangGraph 多智能体工作流

```
用户提问
    │
    ▼
┌─────────────┐
│ 意图识别 Agent │ ──→ 识别问题类型（7 类意图）
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 路由判断     │ ──→ 校园知识 / 闲聊 / 超出范围
└──┬──────┬───┘
   │      │
   │      └──→ 拒绝回答（超出范围/敏感内容）
   │
   ▼
┌─────────────┐
│ 检索 Agent   │ ──→ 混合检索（向量 + 关键词）多知识库集合
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 溯源 Agent   │ ──→ 提取文档来源信息（文件名、页码、知识库）
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────────────────┐
│ 回答生成 Agent │ ──→ │ Markdown 格式化 + 来源汇总 │
└──────┬──────┘     └──────────────────────────┘
       │
       ▼
┌─────────────┐
│ 审核 Agent   │ ──→ 幻觉检测 + 敏感词过滤
└──────┬──────┘
       │
   ┌───┴───┐
   │ 通过   │ 不通过（重试 ≤ 2 次 → 回到回答生成；超过 → 拒绝）
   ▼       ▼
 返回回答   拒绝回答
```

**意图分类**（7 类）：
- `campus_policy` — 校园政策
- `academic_affairs` — 教务管理
- `scholarship` — 奖学金资助
- `campus_life` — 校园生活
- `casual_chat` — 闲聊
- `invalid` — 无效/敏感内容
- `out_of_scope` — 超出校园范围

---

## 4. 核心模块说明

### 4.1 后端目录结构

```
backend/app/
├── main.py                  # FastAPI 应用入口，注册路由与中间件
├── config.py                # Pydantic Settings 配置管理
├── core/
│   ├── llm_factory.py       # LLM 工厂（Ollama/OpenAI 兼容）
│   ├── security.py          # JWT 生成 + bcrypt 密码哈希
│   ├── exceptions.py        # 全局异常处理
│   └── logging.py           # loguru 日志配置
├── db/
│   ├── base.py             # SQLAlchemy 声明性基类
│   └── session.py           # 异步会话工厂 + 建表
├── models/                  # ORM 模型
│   ├── user.py              # 用户
│   ├── chat.py              # 会话 + 消息
│   ├── knowledge_base.py    # 知识库
│   ├── document.py          # 文档
│   ├── summary.py           # 摘要 + 条例 + 考点
│   └── faq.py              # FAQ + 问题记录
├── schemas/                 # Pydantic 请求/响应模型
├── api/v1/                  # FastAPI 路由（11 个模块）
│   ├── auth.py              # 认证
│   ├── chat.py              # 聊天（流式 + 历史 + 重命名）
│   ├── knowledge.py         # 知识库 CRUD
│   ├── document.py          # 文档上传/列表/删除/重索引
│   ├── summary.py           # 文档总结
│   ├── faq.py               # FAQ 管理
│   ├── stats.py             # 仪表盘统计
│   ├── analytics.py         # 数据分析
│   ├── user.py              # 用户管理
│   └── citation.py          # 引用查询
├── services/                # 业务逻辑层
│   ├── chat_service.py      # 聊天编排（SSE + 历史保存 + 问题记录）
│   ├── document_service.py  # 文档处理（异步线程 + 向量化）
│   ├── knowledge_service.py # 知识库 CRUD
│   └── summary_service.py   # 总结生成
├── agents/                  # LangGraph 多智能体
│   ├── state.py             # AgentState + IntentType + Citation
│   ├── graph.py             # StateGraph 构建与编译
│   └── nodes/               # 5 个智能体节点
│       ├── intent_node.py   # 意图识别
│       ├── retrieve_node.py # 文档检索
│       ├── citation_node.py # 溯源提取
│       ├── answer_node.py   # 回答生成
│       └── review_node.py   # 内容审核
└── rag/                     # RAG 系统
    ├── processors/          # 文档解析器（PDF/DOCX/TXT）
    ├── embeddings/          # 嵌入工厂（Ollama/OpenAI/HuggingFace）
    ├── vectorstore/          # ChromaDB 管理
    ├── retrievers/          # 混合检索器（向量 + 关键词）
    ├── prompts/             # 系统提示词 + 回答生成提示词
    ├── summarizer/          # 文档总结（摘要 + 条例 + 考点）
    └── utils/               # 文本清洗 + 递归切片
```

### 4.2 前端目录结构

```
frontend/src/
├── app/                     # Next.js App Router
│   ├── dashboard/           # 学生端
│   │   ├── page.tsx         # 聊天主界面
│   │   └── knowledge/       # 知识库浏览
│   ├── admin/               # 管理端
│   │   ├── page.tsx         # 仪表盘
│   │   ├── documents/       # 文档管理
│   │   ├── knowledge/       # 知识库管理
│   │   ├── users/           # 用户管理
│   │   ├── analytics/       # 数据统计
│   │   └── faq/             # FAQ 管理
│   ├── login/               # 登录页
│   └── register/            # 注册页
├── components/
│   ├── chat/                # 聊天组件（消息列表、输入框、引用列表）
│   ├── layout/              # 布局（学生端侧边栏、管理端头部）
│   ├── summary/             # 文档总结组件
│   ├── knowledge/           # 知识库组件
│   └── ui/                  # 通用 UI 组件
├── lib/
│   ├── api.ts               # Axios 封装 + API 客户端
│   └── hooks/
│       ├── use-chat.ts      # 聊天 Hook（SSE 流式 + 会话管理）
│       └── use-sse.ts       # SSE 连接 Hook（直连后端）
├── store/
│   ├── use-auth-store.ts    # 认证状态
│   └── use-chat-store.ts    # 聊天状态（会话列表 + 消息 + 重命名）
└── types/
    └── index.ts             # TypeScript 类型定义
```

### 4.3 关键设计决策

#### SSE 直连后端
前端 `use-sse.ts` 将 `/api/...` 路径解析为 `http://localhost:8000/api/...` 绝对 URL，绕过 Next.js dev server 的 rewrites 代理。原因：Next.js 代理底层使用 `http-proxy`，会缓冲 `text/event-stream` 响应，导致前端无法实时接收 SSE 数据块。

#### 文档处理异步线程
`document_service._process_and_store_sync` 是同步方法（PDF 解析、向量化、ChromaDB 写入均为 CPU/IO 密集型同步操作），通过 `asyncio.to_thread()` 在独立线程中执行，不阻塞 FastAPI 事件循环，HTTP 响应可立即返回。

#### 动态知识库集合解析
`chat_service._resolve_collection_names` 在用户未指定知识库时，动态查询所有公开知识库的 `collection_name`，避免硬编码集合名。检索和向量化使用同一 Ollama 嵌入模型（`nomic-embed-text`），确保查询向量与文档向量维度一致。

---

## 5. 开发历程与阶段性成果

### 阶段 1：项目规划与架构设计

**成果**：完成项目目录结构设计、依赖选型、启动序列规划、系统架构图绘制。

- 确定技术栈：LangGraph + LangChain + FastAPI + Next.js + ChromaDB + Ollama
- 设计前后端分离架构：FastAPI (8000) + Next.js (3000)
- 规划 6 个开发阶段

### 阶段 2：LangGraph 多智能体核心架构

**成果**：实现 5 个智能体节点的协同工作流。

- 定义 `AgentState` 状态结构（对话历史、意图、检索文档、引用、回答、审核状态）
- 实现 `IntentType` 7 类意图枚举
- 构建 `StateGraph`：意图识别 → 路由判断 → 检索 → 溯源 → 回答生成 → 审核
- 条件路由：审核未通过时回到回答生成重试（最多 2 次），超过则拒绝

### 阶段 3：多源文件解析 + 向量化入库

**成果**：实现 PDF/Word/TXT/Markdown 四种格式的文档解析与向量化。

- PDF 处理器：基于 PyPDF2，支持按页提取文本与页码元数据
- Word 处理器：基于 python-docx，提取段落文本
- TXT/Markdown 处理器：直接读取
- 文本清洗器：去除多余空白、特殊字符
- 递归切片器：按语义边界递归切分，保持上下文完整
- EmbeddingFactory：支持 Ollama / OpenAI / HuggingFace 三种嵌入后端
- ChromaDB 管理器：持久化存储，支持按集合名检索

### 阶段 4：完整后端 API 系统

**成果**：实现 11 个路由模块、52 个 API 端点。

- 认证模块：JWT 登录/注册/刷新/当前用户
- 聊天模块：流式 SSE + 非流式 + 会话 CRUD + 重命名
- 知识库模块：CRUD + 文档数量统计
- 文档模块：上传/列表/删除/重索引 + 处理状态轮询
- 总结模块：摘要/条例/考点查询
- FAQ 模块：CRUD
- 统计模块：仪表盘（用户/知识库/对话/今日提问）
- 分析模块：意图分布/热门问题/无效分析
- 用户管理模块

### 阶段 5：完整前端双端界面

**成果**：实现学生端与管理端完整界面。

**学生端**：
- 聊天主界面（消息列表、输入框、流式输出、引用展示）
- 知识库浏览（公开知识库卡片、文档列表、文档总结）
- 历史会话侧边栏（重命名、删除、切换）
- 登录/注册页面

**管理端**：
- 仪表盘（4 个统计卡片 + 图表）
- 知识库管理（创建/编辑/删除）
- 文档管理（上传/删除/重索引 + 状态轮询）
- 用户管理
- 数据统计（意图分布饼图、热门问题、趋势图）
- FAQ 管理
- 右上角"返回智能问答"导航

### 阶段 6：创新功能

**成果**：实现智能文档总结与热门问题统计。

- **文档摘要生成器**：LLM 生成结构化摘要（标题、主要内容、重要规定）
- **重点条例提取器**：提取关键条款（标题、内容、来源位置、分类、重要性评分）
- **可提问考点生成器**：生成问答对（问题、答案、难度、分类、来源位置）+ 4 级 JSON 解析容错
- **QuestionRecorder**：每次问答自动记录问题、意图、有效性
- **热门问题聚合**：自动统计高频问题生成 FAQ

### 阶段 7：依赖安装与环境配置

**成果**：解决 Windows 环境下的依赖安装问题。

- ChromaDB 安装：`pip install chromadb --only-binary=:all:`（绕过 MSVC 14.0 编译）
- Ollama 本地部署：安装 Ollama → 拉取 qwen2.5:7b + nomic-embed-text → 配置 .env
- 前端依赖安装：`npm install`

### 阶段 8：Bug 修复与功能优化（多轮迭代）

以下按时间顺序记录每轮修复的成果：

#### 第 1 轮：基础功能修复
- **知识库文档数显示 0**：`KnowledgeBaseResponse` 缺少 `document_count` 字段，`list_knowledge_bases()` 未 join Document 表 → 新增字段 + SQL outerjoin
- **用户提问未记录**：`QuestionRecorder` 未集成到聊天流程 → 在 `chat()` 和 `chat_stream()` 中调用 `record()`
- **始终回答"暂无相关信息"**：`retrieve_node.py` 硬编码 `DEFAULT_KNOWLEDGE_BASES = ["campus_default"]` → 改为动态查询公开知识库集合名
- **管理后台无返回按钮**：header.tsx 用户下拉菜单新增"返回智能问答"链接

#### 第 2 轮：学生端知识库 + 检索修复
- **学生端看不到公开知识库**：`use-knowledge-store.ts` 把分页响应当数组处理 → 修复为 `list?.items ?? []`
- **检索极慢/一直加载**：ChromaDB 查询时触发 ONNX 模型下载（79MB, 48KB/s）→ 检索前用 Ollama 预计算查询向量，`chroma_manager.query()` 新增 `query_embedding` 参数绕过 ONNX

#### 第 3 轮：SSE 流式响应修复
- **前端一直加载无法显示回答**：
  - **根因 A**：Next.js rewrites 代理缓冲 SSE 响应 → `use-sse.ts` 新增 `resolveSSEUrl()` 直连后端 `http://localhost:8000`
  - **根因 B**：后端发 `type: "citations"` 前端匹配 `case 'citation'`（单数）→ 修复事件类型对齐
  - **根因 C**：后端 `session` 事件未处理 → 新增 `case 'session'` 捕获 `session_id`
  - **根因 D**：`Citation` 字段名不匹配（`file_name` vs `filename`）→ 类型兼容两种字段名

#### 第 4 轮：对话历史 + 回答格式 + 仪表盘修复
- **对话未自动保存到历史**：
  - `fetchSessions` 错误拆包响应（`res.data.items` → `res.items`）
  - `useChat` 流式结束后未刷新会话列表 → 新增 `fetchSessions()` 调用
  - 占位会话 `id=0` 未清理 → `setCurrentSessionId` 自动移除
  - 闭包陈旧 → 改用 `useChatStore.getState().currentSessionId`
- **回答格式不规范**：重写 `ANSWER_GENERATION_PROMPT` + `SYSTEM_PROMPT`，要求 Markdown 结构 + 来源汇总在末尾
- **仪表盘数据全显示 0**：后端返回 `users`/`knowledge_bases` 前端读 `total_users`/`total_knowledge_bases` → 对齐键名 + 新增 `today_questions` 查询

#### 第 5 轮：会话命名 + 文档上传 + 考点解析
- **历史对话命名功能**：新增 `PATCH /history/{session_id}` 后端端点 + 前端侧边栏行内编辑 UI
- **文档上传 500（间歇性）**：`asyncio.get_event_loop()` 弃用 → 改为 `asyncio.get_running_loop()`
- **考点 JSON 解析失败**：LLM 返回残缺 JSON → 新增 4 级降级解析（直接解析 → JSON 修复 → raw_decode → 逐对象挽救）
- **考点生成失败阻断摘要**：`generate_questions` 异常时 `raise` → 改为 `return []`

#### 第 6 轮：文档上传超时根治
- **上传大文件 500**：
  - **根因**：`_process_and_store` 标记为 `async` 但内部全是同步操作（PDF 解析 ~68 秒），阻塞事件循环导致 HTTP 响应无法发送
  - **修复**：改为同步方法 `_process_and_store_sync`，用 `asyncio.to_thread()` 在独立线程执行
  - 上传现在 < 1 秒返回，前端 5 秒轮询处理状态自动更新

---

## 6. 接手项目后的运行方法

### 6.1 环境要求

| 软件 | 版本 | 说明 |
|------|------|------|
| Python | 3.13+ | 后端运行时 |
| Node.js | 18+ | 前端运行时 |
| Ollama | 最新版 | 本地 LLM 服务 |
| Conda | 任意 | Python 虚拟环境管理（可选） |

### 6.2 完整启动步骤

#### 步骤 1：安装 Ollama 并拉取模型

```powershell
# 安装 Ollama（下载地址 https://ollama.com/download/windows）
ollama --version

# 拉取对话模型（约 4.7GB）
ollama pull qwen2.5:7b

# 拉取嵌入模型（约 274MB）
ollama pull nomic-embed-text

# 验证
ollama list
```

#### 步骤 2：配置后端环境

```powershell
# 激活虚拟环境
conda activate campus

# 安装后端依赖
cd d:\Campus_Assistant\backend
pip install -r requirements.txt

# 如遇 ChromaDB 编译失败
pip install chromadb --only-binary=:all:
```

编辑 `backend/.env`：
```ini
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=qwen2.5:7b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

#### 步骤 3：启动后端

```powershell
cd d:\Campus_Assistant\backend
python run.py
```

后端启动后：
- 服务地址：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 自动创建 SQLite 数据库和初始管理员账号

#### 步骤 4：启动前端

```powershell
cd d:\Campus_Assistant\frontend
npm install        # 首次
npm run dev
```

前端启动后访问：http://localhost:3000

#### 步骤 5：登录并测试

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123456 | 管理员 |

**测试流程**：
1. 登录系统
2. 管理端 → 知识库管理 → 创建知识库（勾选"公开"）
3. 文档管理 → 上传校园文档（PDF/Word/TXT）
4. 等待文档处理完成（状态自动从"处理中"变为"已完成"）
5. 右上角 → "返回智能问答"
6. 在聊天界面提问，观察流式回答与来源溯源
7. 侧边栏 → hover 历史会话 → 重命名
8. 管理端 → 仪表盘 → 查看统计数据

### 6.3 停止服务

- 后端：`Ctrl + C`（终端中）
- 前端：`Ctrl + C`（终端中）
- Ollama：服务自动后台运行，无需手动停止

### 6.4 数据重置

如需清空所有数据重新开始：

```powershell
# 删除数据库
del d:\Campus_Assistant\backend\data\sqlite\campus.db

# 删除向量数据库
rmdir /s /q d:\Campus_Assistant\backend\data\chroma

# 删除上传文件
rmdir /s /q d:\Campus_Assistant\backend\data\uploads

# 重启后端，自动重建数据库和初始管理员
cd d:\Campus_Assistant\backend
python run.py
```

---

## 7. 已知限制与注意事项

### 7.1 LLM 模型
- 当前使用 `qwen2.5:7b`（约 4.7GB），需要至少 8GB 内存
- 文档过长时（> 4000 字），条例提取和考点生成仅使用前 4000 字（LLM 上下文限制）
- 可在 `backend/.env` 中切换为更强大的模型（如 `qwen2.5:14b`）或云端 API（OpenAI/DeepSeek）

### 7.2 文件上传
- 支持格式：PDF、Word (.docx)、TXT、Markdown
- 最大文件大小：50MB（可在 `.env` 中修改 `MAX_FILE_SIZE`）
- PDF 解析使用 PyPDF2，复杂排版可能丢失格式

### 7.3 向量检索
- 嵌入模型为 `nomic-embed-text`（768 维），本地运行无需网络
- ChromaDB 持久化存储在 `backend/data/chroma/`
- 检索采用混合策略：向量相似度 + 关键词匹配

### 7.4 前端 SSE
- SSE 请求直连后端 `http://localhost:8000`，绕过 Next.js 代理
- 生产环境需通过 `NEXT_PUBLIC_API_BASE_URL` 环境变量配置后端地址
- 后端 CORS 已配置允许 `localhost:3000`

### 7.5 数据库
- 使用 SQLite（`backend/data/sqlite/campus.db`），便于本地开发和演示
- 生产环境建议更换为 PostgreSQL
- 数据库会话使用异步引擎（`aiosqlite`）

---

> 本文档由开发团队维护，最后更新于 2026-06-26。
