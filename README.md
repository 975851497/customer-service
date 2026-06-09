# 教育智能客服系统 (Edu-Assist)

面向在线教育行业的智能客服系统，基于大语言模型（LLM）进行对话回合规划，自动识别学员意图并执行业务流程，涵盖课程咨询、订单查询、学习进度跟踪、退款申请、工单提交等教育客服场景。

## 核心能力

| 能力 | 说明 |
|------|------|
| 课程咨询 | 查询课程系列信息、班次安排、价格和授课方式 |
| 订单查询 | 根据订单号查询订单状态、支付情况和报名课程 |
| 学习进度查询 | 查询考勤、视频完成情况、作业提交和考试成绩 |
| 退款申请 | 多轮对话收集订单号和退款原因，提交退款申请 |
| 工单提交 | 收集工单类型、关联订单号和问题描述，创建服务工单 |
| 闲聊应答 | 处理问候、感谢等非任务型日常对话 |
| 意图澄清 | 当无法准确判断用户意图时主动澄清 |
| 任务中断/恢复 | 支持在多个任务之间切换和恢复 |
| SSE 流式输出 | LLM Token 级流式响应，前端打字机效果 |

## 技术栈

| 技术 | 用途 |
|------|------|
| **Python 3.11+** | 开发语言 |
| **FastAPI** | Web API 框架 |
| **LangChain + LangChain-OpenAI** | LLM 调用与结构化输出 |
| **SQLAlchemy 2.0 (async)** | 数据库 ORM |
| **aiomysql** | MySQL 异步驱动 |
| **Pydantic / pydantic-settings** | 数据校验与配置管理 |
| **httpx** | 异步 HTTP 客户端（调用教育数据 API） |
| **Jinja2** | 模板渲染（提示词模板 + Action 响应生成） |
| **uvicorn** | ASGI 服务器 |
| **PyYAML** | 流程定义文件格式 |
| **uv** | Python 包管理器 |
| **Vue 3 + Vite** | 前端框架（独立项目） |

## 系统架构

### 整体部署拓扑

```
┌─────────────────────────────────────────────────────────────────┐
│                    浏览器 (localhost:5173)                       │
│                    Vue 3 前端应用                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
              Vite Proxy（开发模式）
          ┌────────────┴────────────┐
          │                         │
  /api/*                    /api/v1/*
          │                         │
          ▼                         ▼
┌──────────────────┐    ┌──────────────────────────────┐
│ 智能客服服务       │    │ 教育数据服务                   │
│ Python FastAPI    │    │ Python FastAPI + MySQL       │
│ :18082            │    │ :8000 （Docker 部署）         │
│ ┌──────────────┐  │    │                              │
│ │ LLM (通义千问)│  │    │ 课程·班次·订单·学习进度       │
│ └──────────────┘  │    │                              │
│ ┌──────────────┐  │    │                              │
│ │ MySQL 状态存储│  │    │                              │
│ └──────────────┘  │    │                              │
└──────────────────┘    └──────────────────────────────┘
```

### 六层架构

```
┌─────────────────────────────────────────────────────────────┐
│                      API 层 (api/)                           │
│               FastAPI 路由 · 请求/响应 Schema                 │
│         POST /api/chat · POST /api/chat/stream · ...         │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                     服务层 (service/)                        │
│                DialogueService · 编排核心流程                  │
│             加载状态 → 引擎处理 → 持久化                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                     引擎层 (engine/)                         │
│          DialogueEngine · Builder · 系统组件组装              │
│       会话管理 · 消息路由 · 回合生命周期 · 流式输出            │
└──────┬──────────┬──────────┬──────────┬─────────────────────┘
       │          │          │          │
┌──────▼──┐ ┌─────▼─────┐ ┌─▼────────┐ ┌▼──────────────┐
│ 规划层  │ │ 任务层    │ │ 知识层    │ │ 闲聊/澄清层   │
│ plan/   │ │ task/     │ │knowledge/ │ │ chitchat/     │
│ Turn    │ │ Flow      │ │ Course    │ │ clarify/      │
│ Planner │ │ Executor  │ │ Provider  │ │               │
└─────────┘ └─────┬─────┘ └──────────┘ └───────────────┘
                  │
          ┌───────┴────────┐
          │  动作层        │
          │ task/action/   │
          │ · builtin/     │
          │ · custom/      │
          └───────┬────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                 基础设施层 (infrastructure/)                  │
│      LLM · 数据库 · HTTP 客户端 · 配置管理                    │
└─────────────────────────────────────────────────────────────┘
```

### 消息处理流程

```
用户消息 (HTTP POST /api/chat 或 POST /api/chat/stream)
       │
       ▼
  [API 层] 接收请求，转换为领域消息
       │
       ▼
  [服务层] DialogueService
       │
       ├── 1. DialogueStateRepository.load_state(sender_id)
       │     从 MySQL 加载对话状态 (JSON 反序列化)
       │
       ├── 2. DialogueEngine.process_message(state, user_message)
       │     │
       │     ├── 2.1 会话管理
       │     │    新会话 / 1 小时超时关闭 / 复用当前会话
       │     │
       │     ├── 2.2 创建待决回合 (Pending Turn)
       │     │
       │     ├── 2.3 消息路由
       │     │     │
       │     │     ├── 对象消息（订单/班次卡片）
       │     │     │    └── 自动映射为 Slot 值，跳过 LLM
       │     │     │
       │     │     └── 文本消息 → TurnPlanner 调用 LLM 预测
       │     │              │
       │     │              ├── task 路径 → TaskHandler
       │     │              │    ├── CommandProcessor 处理命令
       │     │              │    │   (StartFlow / SetSlots / CancelFlow / ResumeFlow)
       │     │              │    └── FlowExecutor 执行 YAML 流程
       │     │              │        ├── collect → 收集用户输入
       │     │              │        ├── action → 执行业务动作
       │     │              │        └── end → 流程结束
       │     │              │
       │     │              ├── knowledge 路径 → KnowledgeHandler
       │     │              │    ├── KnowledgeProvider 检索多源数据
       │     │              │    │   (课程/班次/订单/进度/FAQ)
       │     │              │    └── LLM 生成自然语言回复
       │     │              │
       │     │              ├── chitchat 路径 → ChitchatHandler
       │     │              │    └── LLM 闲聊回复
       │     │              │
       │     │              └── clarify 路径 → ClarifyResponder
       │     │                   └── 意图澄清回复
       │     │
       │     └── 2.4 提交待决回合，返回 ProcessResult
       │
       └── 3. DialogueStateRepository.save_state(state)
             状态序列化，MySQL upsert
```

### 流式输出流程 (SSE)

```
用户消息 → POST /api/chat/stream
       │
       ▼
  [DialogueService.process_message_stream()]
       │
       ├── 加载状态
       ├── 引擎流式处理 → 产出事件
       │     │
       │     ├── {"type": "header", "sender_id": "...", "message_id": "..."}
       │     ├── {"type": "chunk", "text": "token"}  ← 实时 LLM token
       │     ├── {"type": "chunk", "text": "token"}
       │     ├── ...
       │     └── {"type": "done", "text": ""}
       │
       └── 保存状态（finally 保证）
       │
       ▼
  [前端 SSE 解析] → 逐 chunk 追加到气泡，打字机效果
```

## 核心概念

### 领域消息

| 消息类型 | 说明 |
|---------|------|
| `UserMessage` | 用户消息，包含文本(`TEXT`)或结构化对象(`OBJECT`) |
| `BotMessage` | 机器人回复，支持文本和结构化对象 |
| `MessageObject` | 结构化对象（订单、班次、课程系列等） |
| `ProcessResult` | 消息处理结果 |

### 对话状态 (DialogueState)

```
DialogueState
├── sender_id             # 发送者标识
├── active_task           # 当前活跃的用户任务
│   ├── flow_id           # 流程 ID
│   ├── step_id           # 当前步骤
│   └── slots{}           # 已收集的参数
├── paused_tasks[]        # 被暂停的用户任务栈（支持多级中断/恢复）
├── active_system_task    # 当前活跃的系统任务
├── focused_object        # 用户当前聚焦的结构化对象
├── sessions[]            # 历史会话列表
├── current_session_id    # 当前会话 ID
└── pending_turn          # 处理中的待决回合
```

### 回合规划 (Turn Plan)

LLM 对用户消息的规划结果，决定响应策略：

```python
class TurnPlan(BaseModel):
    task: TaskTurnPlan | None = None       # 需要执行业务流程
    knowledge: KnowledgeTurnPlan | None = None  # 需要查询知识
    chitchat: ChitchatTurnPlan | None = None    # 闲聊/问候
```

- **同一回合只能有一个赛道非空**（由 `TurnPlanValidator` 保证）
- **Task 赛道**：需执行业务流程（查订单、退款、提工单）
- **Knowledge 赛道**：需查询知识库（课程信息、政策等）
- **Chitchat 赛道**：纯闲聊或问候
- 规划无效时自动进入 **Clarify 澄清**路径

### 流程 (Flow)

YAML 定义的业务流程，支持声明式步骤编排：

| 步骤类型 | 说明 |
|---------|------|
| `start` | 流程起始，指向第一个步骤 |
| `collect` | 收集用户输入的 Slot 值（支持自动聚焦对象填充） |
| `action` | 执行一个原子动作（查询 API、生成回复等） |
| `end` | 流程结束 |

**流程配置示例**（`flow_config/user_flows.yml`）：
```yaml
flows:
  order_status_query:
    name: 订单查询
    steps:
      - id: start
        type: start
        next: ask_order_number

      - id: ask_order_number
        type: collect
        slot_name: order_number
        response:
          text: "请告诉我你的订单号。"
        next: lookup_order

      - id: lookup_order
        type: action
        action: action_lookup_order
        args:
          order_number: "{{ slots.order_number }}"
        next: show_order

      - id: show_order
        type: action
        action: action_response
        args:
          mode: rephrase
          text: "订单{{ slots.order_number }}查询结果如上。"
        next: end

      - id: end
        type: end
```

### 动作系统

**内置动作：**

| 动作名称 | 说明 |
|---------|------|
| `action_listen` | 等待用户输入（暂停流程） |
| `action_response` | 生成回复：`static` 静态 / `rephrase` LLM 润色 / `llm` LLM 生成 |

**自定义业务动作：**

| 动作名称 | 说明 | 调用的教育 API |
|---------|------|---------------|
| `action_lookup_course_series` | 查询课程系列信息 | `GET /api/v1/series` |
| `action_lookup_cohort` | 查询班次详情 | `GET /api/v1/cohorts/{id}` |
| `action_lookup_order` | 查询订单状态 | `GET /api/v1/orders/{id}` |
| `action_lookup_progress` | 查询学习进度 | `GET /api/v1/me/cohorts/{id}/progress` |
| `action_create_refund` | 创建退款申请 | `POST /api/v1/order-items/{id}/refund-requests` |
| `action_create_ticket` | 创建服务工单 | `POST /api/v1/service-tickets` |

### 知识提供者

| 提供者 | 数据来源 | 说明 |
|--------|---------|------|
| `CourseSeriesProvider` | `api.course_series` | 课程系列信息，支持渐进式关键词搜索 |
| `CohortProvider` | `api.cohort` | 班次详情、价格、开课时间 |
| `OrderProvider` | `api.order` | 用户订单列表与状态 |
| `ProgressProvider` | `api.progress` | 考勤/视频/作业/考试多维度进度 |
| `FAQProvider` | `faq.default` | FAQ 知识库（退款政策等） |

## API 接口

### 基础信息

| 项目 | 说明 |
|------|------|
| 基础路径 | `http://{host}:{port}` |
| 默认端口 | `18082` |
| 数据格式 | JSON，SSE |

### 1. 发送对话消息（普通）

`POST /api/chat`

**文本消息请求：**
```json
{
  "sender_id": "user_001",
  "text": "帮我查一下订单123456的状态"
}
```

**对象消息请求（点击卡片）：**
```json
{
  "sender_id": "user_001",
  "object": {
    "type": "order",
    "id": "123456",
    "title": "订单 #123456",
    "attributes": {"amount": "2999.00", "status": "已支付"}
  }
}
```

**成功响应：**
```json
{
  "sender_id": "user_001",
  "message_id": "uuid",
  "messages": [
    {"text": "订单查询结果...", "object": null}
  ]
}
```

### 2. 发送对话消息（SSE 流式）

`POST /api/chat/stream`

请求体格式同上。响应为 Server-Sent Events 流：

```
data: {"type": "header", "sender_id": "1", "message_id": "uuid"}
data: {"type": "chunk", "text": "您"}
data: {"type": "chunk", "text": "好"}
data: {"type": "chunk", "text": "，"}
data: {"type": "chunk", "text": "我"}
data: {"type": "chunk", "text": "是"}
data: {"type": "chunk", "text": "教"}
data: {"type": "chunk", "text": "育"}
data: {"type": "chunk", "text": "智"}
data: {"type": "chunk", "text": "能"}
data: {"type": "chunk", "text": "客"}
data: {"type": "chunk", "text": "服"}
data: {"type": "chunk", "text": "。"}
data: {"type": "done", "text": ""}
data: [DONE]
```

| 事件类型 | 说明 |
|---------|------|
| `header` | 消息头，包含 sender_id 和 message_id |
| `chunk` | LLM 实时生成的文本片段 |
| `done` | 消息完成标记 |
| `error` | 处理异常信息 |
| `[DONE]` | 流结束标记 |

### 3. 获取聊天历史

`GET /api/chat/history?sender_id=user_001`

```json
{
  "sender_id": "user_001",
  "messages": [
    {"role": "user", "text": "你好", "object": null},
    {"role": "bot", "text": "你好！我是教育智能客服助手...", "object": null}
  ]
}
```

### 4. 获取会话状态

`GET /api/chat/session?sender_id=user_001`

```json
{
  "sender_id": "user_001",
  "session_id": "uuid",
  "has_active_task": true,
  "active_task_flow_id": "order_status_query",
  "active_task_name": "订单查询",
  "slots": {"order_number": "ORD123"},
  "paused_task_count": 0
}
```

### 5. 健康检查

`GET /health`

```json
{"status": "ok", "service": "edu-assist"}
```

## 业务流程

### 用户流程

| 流程 ID | 说明 | 步骤 |
|---------|------|------|
| `course_consultation` | 课程咨询：查课程 → 推荐班次 → 引导选择 | 6步 |
| `order_status_query` | 订单查询：收集订单号 → 查询状态 → 展示结果 | 5步 |
| `learning_progress_query` | 学习进度查询：收集班次 → 查询多维度进度 | 5步 |
| `refund_request` | 退款申请：订单号 → 退款原因 → 退款类型 → 提交 | 7步 |
| `ticket_submission` | 工单提交：工单类型 → 订单号 → 问题描述 → 创建 | 7步 |
| `human_handoff` | 转人工客服 | 3步 |

### 系统流程

| 流程 ID | 触发时机 |
|---------|---------|
| `system_task_started` | 启动新任务后，通知用户 |
| `system_task_resumed` | 恢复暂停任务后，通知用户 |
| `system_task_interrupted` | 任务被中断时，通知用户 |
| `system_task_canceled` | 任务被取消时，确认取消 |
| `system_collect_information` | 需要收集信息时，等待用户输入 |
| `system_cannot_handle` | 无法处理时，兜底回复 |
| `system_completed` | 任务完成标记 |

### 命令

| 命令 | 说明 |
|------|------|
| `start_flow` | 启动指定流程，可同时预填槽位 |
| `set_slots` | 设置当前任务的槽位值 |
| `cancel_flow` | 取消当前流程 |
| `resume_flow` | 从暂停栈恢复流程 |

## 环境要求

| 依赖 | 版本要求 |
|------|---------|
| Python | >= 3.11 |
| MySQL | 8.0+（支持 utf8mb4） |
| uv | 最新版本 |
| Node.js | >= 18（前端） |

## 环境变量配置

| 变量 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| `LLM_MODEL` | 是 | LLM 模型名称 | `qwen-plus` |
| `LLM_BASE_URL` | 是 | API 地址（OpenAI 兼容格式） | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `LLM_API_KEY` | 是 | API 密钥 | - |
| `EDU_API_BASE_URL` | 是 | 教育数据 API 地址 | `http://127.0.0.1:8000` |
| `DATABASE_URL` | 是 | MySQL 连接 URL | `mysql+aiomysql://root:root@127.0.0.1:3306/edu_assist?charset=utf8mb4` |
| `APP_HOST` | 否 | 监听地址 | `0.0.0.0` |
| `APP_PORT` | 否 | 监听端口 | `18082` |

## 快速启动

### 1. 启动依赖服务

```bash
# 启动 MySQL 和 edu-data（推荐 Docker 部署）
cd 需求/教育/edu-data/docker
docker-compose up -d

# 或手动启动 edu-data
cd 需求/教育/edu-data
uv run python init_db.py    # 初始化数据库并导入样本数据
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 启动智能客服服务

```bash
# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 LLM_API_KEY 和数据库配置

# 安装依赖
uv sync

# 启动服务
uv run uvicorn main:app --host 0.0.0.0 --port 18082 --reload

# 验证
curl -X POST "http://127.0.0.1:18082/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"sender_id": "test_user", "text": "你好"}'
```

### 3. 启动前端（可选）

```bash
cd customer-service-frontend
npm install
npm run dev
# 访问 http://127.0.0.1:5173
```

## 常见场景示例

### 场景一：课程咨询

```
学员 → "Python 全栈课程大概是什么情况？"
  → 知识赛道：搜索课程信息
  → 返回课程列表、班次安排、价格
  → 引导选择具体班次了解更多
```

### 场景二：多轮订单查询

```
学员 → "帮我查一下订单"
  → task 赛道：启动 order_status_query 流程
  → collect: "请告诉我你的订单号。"
学员 → "ORD20240401005"
  → action_lookup_order → 查询订单状态
  → 返回订单详情
```

### 场景三：任务中断与恢复

```
学员 → "我要退款"
  → 启动 refund_request 流程（活跃任务）
  → collect: "请提供要退款的订单号。"
学员 → "等一下，先帮我查一下物流"
  → LLM 规划为新流程 → 中断退款，启动物流查询
  → 物流查询结束后，自动恢复退款流程
```

### 场景四：结构化对象消息

```
学员（点击订单卡片）→ 发送结构化对象
  → engine 自动识别对象类型
  → 映射到当前收集槽位（order_number）
  → 继续执行流程
```

## 项目目录结构

```
edu-assist/
├── main.py                          # 应用入口（FastAPI）
├── pyproject.toml                   # 项目依赖
├── Makefile                         # 常用命令
├── Dockerfile                       # Docker 构建
├── docker-compose.yml               # Docker Compose
├── .env / .env.example              # 环境变量配置
├── flow_config/
│   ├── user_flows.yml               # 用户侧业务流程定义
│   └── system_flows.yml             # 系统侧流程定义
├── static/                          # 静态文件（调试页面）
├── edu_assist/                      # 核心源码包
│   ├── __init__.py
│   ├── conf/
│   │   └── config.py                # 配置管理（pydantic-settings）
│   ├── domain/
│   │   ├── messages.py              # 领域消息模型
│   │   └── state.py                 # 对话状态聚合根
│   ├── infrastructure/
│   │   ├── llm.py                   # LLM 调用（非流式 + 流式）
│   │   ├── database.py              # 数据库引擎工厂
│   │   └── http_client.py           # HTTP 客户端（httpx）
│   ├── models/
│   │   └── dialogue_state.py        # SQLAlchemy ORM 模型
│   ├── repository/
│   │   └── state_repository.py      # 状态持久化仓库
│   ├── service/
│   │   └── dialogue_service.py      # 对话服务编排
│   ├── engine/
│   │   ├── engine.py                # 对话引擎（含流式处理）
│   │   └── builder.py               # 引擎构建器（组合根）
│   ├── api/
│   │   ├── routes.py                # HTTP 路由
│   │   └── schemas.py               # 请求/响应 Schema
│   ├── plan/
│   │   ├── planner.py               # 回合规划器（LLM 调用）
│   │   └── validator.py             # 规划验证器
│   ├── knowledge/
│   │   ├── handler.py               # 知识问答处理器（含流式）
│   │   └── provider.py              # 知识提供者注册表
│   ├── chitchat/
│   │   └── handler.py               # 闲聊处理器（含流式）
│   ├── clarify/
│   │   └── handler.py               # 意图澄清处理器（含流式）
│   ├── prompts/
│   │   ├── prompt_loader.py         # 提示词加载器
│   │   ├── history_builder.py       # 对话历史构建器
│   │   └── jinja2/                  # Jinja2 模板
│   │       ├── turn_plan.jinja2     # 回合规划提示词
│   │       ├── knowledge_respond.jinja2  # 知识回复提示词
│   │       ├── chitchat_respond.jinja2  # 闲聊回复提示词
│   │       └── clarify_respond.jinja2   # 澄清回复提示词
│   └── task/
│       ├── command.py               # 命令处理器
│       ├── handler.py               # 任务处理器
│       ├── flow/
│       │   ├── models.py            # 流程模型
│       │   ├── steps.py / links.py  # 步骤与链接定义
│       │   ├── loader.py            # YAML 加载器
│       │   └── executor.py          # 流程执行引擎
│       └── action/
│           ├── base.py              # Action 抽象基类
│           ├── registry.py          # 动作注册表
│           ├── runner.py            # 动作运行器
│           ├── builder.py           # 动作注册构建
│           ├── builtin/
│           │   ├── listen.py        # action_listen
│           │   └── response.py      # action_response
│           └── custom/
│               ├── shared.py        # 共享 API 工具
│               ├── lookup_course_series.py   # 课程查询
│               ├── lookup_cohort.py          # 班次查询
│               ├── lookup_order.py           # 订单查询
│               ├── lookup_progress.py         # 学习进度
│               ├── create_refund.py           # 退款创建
│               └── create_ticket.py           # 工单创建
└── 需求/                             # 项目文档
    ├── doc/                         # 技术设计文档（13篇）
    │   ├── 01-项目概述.md
    │   ├── 02-系统架构.md
    │   ├── ...
    │   └── 13-状态管理与持久化.md
    └── 教育/
        ├── 需求说明.md               # 需求规格说明
        └── edu-data/                 # 教育数据 API 服务
            ├── app/                  # FastAPI 应用
            ├── sql/                  # 数据库建表 SQL
            └── seeds/                # 样本数据（CSV）
```

## 扩展指南

### 新增业务流程

1. 在 `flow_config/user_flows.yml` 中定义流程步骤（支持 collect / action / 条件跳转）
2. 如需新的动作，在 `edu_assist/task/action/custom/` 下新建文件
3. 系统启动时自动发现并注册动作

### 新增知识意图

在 `edu_assist/engine/builder.py` 的 `build_dialogue_engine()` 中添加：

```python
provider_registry.register_intent(
    "intent_id",                     # 意图唯一标识
    description="意图描述文本",        # 用于 LLM 识别
    provider_ids=["api.provider_id"], # 关联的知识提供者
)
```

### 新增自定义动作

```python
from edu_assist.task.action.base import Action, ActionResult

class MyAction(Action):
    name = "action_my_action"

    async def run(self, state, action_kwargs):
        # 执行业务逻辑
        return ActionResult(
            messages=[BotMessage(text="处理结果")],
            slot_updates={"slot_name": "value"},
        )
```

### 新增知识提供者

```python
class MyProvider(KnowledgeProvider):
    provider_id = "api.my_provider"

    async def retrieve(self, state) -> list[str]:
        # 检索知识，返回文本块列表
        return ["知识内容"]
```

## 设计要点

1. **全量序列化**：对话状态（DialogueState）整体序列化为 JSON，按 sender_id 独立存储，支持会话恢复和历史回溯
2. **回合规划**：每条用户消息经 LLM 规划输出结构化 TurnPlan，保证单一赛道执行的确定性
3. **命令驱动**：Task 赛道通过命令（StartFlow / SetSlots / CancelFlow / ResumeFlow）驱动状态变更，与流程执行解耦
4. **声明式流程**：YAML 定义业务流程，支持 slot 自动填充（聚焦对象映射）、条件跳转、多步编排，新增流程无需修改代码
5. **任务堆栈**：支持多级任务中断/恢复（paused_tasks 栈），对话可灵活切换上下文
6. **流式输出**：LLM Token 级 SSE 推送，前端实时渲染打字机效果
