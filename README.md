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

## 系统架构

### 六层架构

```
┌─────────────────────────────────────────────────────────────┐
│                      API 层 (api/)                           │
│               FastAPI 路由 · 请求/响应 Schema                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                     服务层 (service/)                        │
│                DialogueService · 编排核心流程                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                     引擎层 (engine/)                         │
│          DialogueEngine · Builder · 系统组件组装              │
└──────┬──────────┬──────────┬──────────┬─────────────────────┘
       │          │          │          │
┌──────▼──┐ ┌─────▼─────┐ ┌─▼────────┐ ┌▼──────────────┐
│ 规划层  │ │ 任务层    │ │ 知识层    │ │ 闲聊/澄清层   │
│ plan/   │ │ task/     │ │knowledge/ │ │ chitchat/     │
│         │ │           │ │           │ │ clarify/      │
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
用户消息 (HTTP POST)
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
       │     ├── 2.1 会话管理：创建/复用/关闭会话
       │     ├── 2.2 创建待决回合
       │     │
       │     ├── 2.3 消息路由
       │     │     │
       │     │     ├── 对象消息 → 自动映射为 Slot 值
       │     │     │
       │     │     └── 文本消息 → TurnPlanner 预测
       │     │            │
       │     │            ├── task 路径 → TaskHandler
       │     │            │    ├── CommandProcessor 处理命令
       │     │            │    └── FlowExecutor 执行流程
       │     │            │
       │     │            ├── knowledge 路径 → KnowledgeHandler
       │     │            │    └── 检索知识 → 生成回复
       │     │            │
       │     │            ├── chitchat 路径 → ChitchatHandler
       │     │            │
       │     │            └── clarify 路径 → ClarifyResponder
       │     │
       │     └── 2.4 提交待决回合，返回 ProcessResult
       │
       └── 3. DialogueStateRepository.save_state(state)
             状态序列化，MySQL upsert
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
├── paused_tasks[]        # 被暂停的用户任务栈
├── active_system_task    # 当前活跃的系统任务
├── focused_object        # 用户当前聚焦的结构化对象
├── sessions[]            # 历史会话列表
├── current_session_id    # 当前会话 ID
└── pending_turn          # 处理中的待决回合
```

### 回合规划 (Turn Plan)

LLM 对用户消息的规划结果，决定响应策略：

- **Task 赛道**：需要执行业务流程（查订单、查进度、退款等）
- **Knowledge 赛道**：需要查询知识库信息（课程信息、政策等）
- **Chitchat 赛道**：纯闲聊或问候

### 流程 (Flow)

YAML 定义的业务流程，支持步骤编排：

| 步骤类型 | 说明 |
|---------|------|
| `start` | 流程起始 |
| `action` | 执行一个动作 |
| `collect` | 收集用户输入的 Slot 值 |
| `end` | 流程结束 |

## 业务流程

### 用户流程

| 流程 ID | 说明 | 步骤数 |
|---------|------|--------|
| `course_consultation` | 课程咨询：查课程 → 推荐班次 | 6步 |
| `order_status_query` | 订单查询：收集订单号 → 查询状态 | 5步 |
| `learning_progress_query` | 学习进度查询：收集班次 → 查询进度 | 5步 |
| `refund_request` | 退款申请：订单号 → 退款原因 → 退款类型 → 提交 | 7步 |
| `ticket_submission` | 工单提交：工单类型 → 订单号 → 问题描述 → 创建 | 7步 |
| `human_handoff` | 转人工客服 | 3步 |

### 系统流程

| 流程 ID | 触发时机 |
|---------|---------|
| `system_task_started` | 启动新任务后 |
| `system_task_resumed` | 恢复暂停任务后 |
| `system_task_interrupted` | 任务被中断时 |
| `system_task_canceled` | 任务被取消时 |
| `system_collect_information` | 需要收集信息时 |
| `system_cannot_handle` | 无法处理时 |
| `system_completed` | 任务完成标记 |

## 动作系统

### 内置动作

| 动作名称 | 说明 |
|---------|------|
| `action_listen` | 等待用户输入（暂停流程） |
| `action_response` | 生成回复，支持 static / rephrase / llm 三种模式 |

### 自定义业务动作

| 动作名称 | 说明 | 调用的教育 API |
|---------|------|---------------|
| `action_lookup_course_series` | 查询课程系列信息 | `GET /api/v1/series` |
| `action_lookup_cohort` | 查询班次详情 | `GET /api/v1/cohorts/{id}` |
| `action_lookup_order` | 查询订单状态 | `GET /api/v1/orders/{id}` |
| `action_lookup_progress` | 查询学习进度 | `GET /api/v1/me/cohorts/{id}/progress` |
| `action_create_refund` | 创建退款申请 | `POST /api/v1/order-items/{id}/refund-requests` |
| `action_create_ticket` | 创建服务工单 | `POST /api/v1/service-tickets` |

## API 接口

### 基础信息

| 项目 | 说明 |
|------|------|
| 基础路径 | `http://{host}:{port}` |
| 默认端口 | `18082` |
| 数据格式 | JSON |

### 1. 发送对话消息

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

### 2. 获取聊天历史

`GET /api/chat/history?sender_id=user_001`

### 3. 获取会话状态

`GET /api/chat/session?sender_id=user_001`

### 4. 健康检查

`GET /health`

### 请求示例

```bash
# 课程咨询
curl -X POST "http://127.0.0.1:18082/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"sender_id": "user_001", "text": "Python全栈课程是什么？"}'

# 查询订单
curl -X POST "http://127.0.0.1:18082/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"sender_id": "user_001", "text": "帮我查下订单 ORD20240401005"}'

# 学习进度查询
curl -X POST "http://127.0.0.1:18082/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"sender_id": "user_001", "text": "我在Python全栈第5期的学习进度怎么样？"}'

# 退款申请
curl -X POST "http://127.0.0.1:18082/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"sender_id": "user_001", "text": "我要退款"}'

# 闲聊
curl -X POST "http://127.0.0.1:18082/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"sender_id": "user_001", "text": "你好"}'
```

## 环境要求

| 依赖 | 版本要求 |
|------|---------|
| Python | >= 3.11 |
| MySQL | 8.0+（支持 utf8mb4） |
| uv | 最新版本 |

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

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 LLM_API_KEY 和数据库配置

# 2. 安装依赖
uv sync

# 3. 初始化数据库（需先创建 MySQL 数据库）
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS edu_assist CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 4. 启动服务
uv run uvicorn main:app --host 0.0.0.0 --port 18082 --reload

# 5. 验证部署
curl -X POST "http://127.0.0.1:18082/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"sender_id": "test_user", "text": "你好"}'
```

## 外部依赖

系统依赖 **edu-data** 业务数据 API 服务提供实时数据查询，需要先启动该服务：

```bash
# edu-data 启动方式（在 需求/教育/edu-data 目录下）
cd 需求/教育/edu-data

# 配置 .env（数据库连接等）
# 初始化数据库并导入样本数据
uv run python init_db.py

# 启动教育数据 API
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

edu-data 服务提供的 API 端点：

| 接口 | 用途 |
|------|------|
| `GET /api/v1/series` | 课程系列列表 |
| `GET /api/v1/series/{id}` | 课程系列详情 |
| `GET /api/v1/series/{id}/cohorts` | 班次列表 |
| `GET /api/v1/cohorts/{id}` | 班次详情 |
| `GET /api/v1/orders/{id}` | 订单详情 |
| `GET /api/v1/me/cohorts/{id}/progress` | 学习进度 |
| `POST /api/v1/order-items/{id}/refund-requests` | 创建退款 |
| `POST /api/v1/service-tickets` | 创建工单 |

## 项目目录结构

```
edu-assist/
├── main.py                          # 应用入口
├── pyproject.toml                   # 项目依赖
├── .env / .env.example              # 环境变量配置
├── flow_config/
│   ├── user_flows.yml               # 用户侧业务流程
│   └── system_flows.yml             # 系统侧流程
└── edu_assist/                      # 核心源码包
    ├── conf/config.py               # 配置管理
    ├── domain/
    │   ├── messages.py              # 领域消息模型
    │   └── state.py                 # 对话状态模型
    ├── infrastructure/
    │   ├── llm.py                   # LLM 基础设施
    │   ├── database.py              # 数据库引擎
    │   └── http_client.py           # HTTP 客户端
    ├── models/dialogue_state.py     # ORM 模型
    ├── repository/state_repository.py  # 状态持久化
    ├── service/dialogue_service.py     # 对话服务
    ├── engine/
    │   ├── engine.py                # 对话引擎
    │   └── builder.py               # 引擎构建器（组合根）
    ├── api/
    │   ├── routes.py                # HTTP 路由
    │   └── schemas.py               # 请求/响应 Schema
    ├── plan/
    │   ├── planner.py               # 回合规划器
    │   └── validator.py             # 规划验证器
    ├── knowledge/
    │   ├── handler.py               # 知识问答处理器
    │   └── provider.py              # 知识提供者注册表
    ├── chitchat/handler.py          # 闲聊处理
    ├── clarify/handler.py           # 意图澄清
    ├── prompts/
    │   ├── prompt_loader.py         # 提示词加载器
    │   ├── history_builder.py       # 历史构建器
    │   └── jinja2/                  # Jinja2 模板
    └── task/
        ├── command.py               # 命令处理
        ├── handler.py               # 任务处理器
        ├── flow/
        │   ├── models.py            # 流程模型
        │   ├── steps.py / links.py  # 步骤与链接
        │   ├── loader.py            # YAML 加载器
        │   └── executor.py          # 流程执行器
        └── action/
            ├── base.py / registry.py / runner.py / builder.py
            ├── builtin/             # 内置动作
            └── custom/              # 自定义业务动作
                ├── shared.py                    # 共享 API 工具
                ├── lookup_course_series.py      # 课程查询
                ├── lookup_cohort.py             # 班次查询
                ├── lookup_order.py              # 订单查询
                ├── lookup_progress.py           # 学习进度
                ├── create_refund.py             # 退款创建
                └── create_ticket.py             # 工单创建
```

## 扩展指南

### 新增业务流程

1. 在 `flow_config/user_flows.yml` 中定义流程步骤
2. 如需新的动作，在 `edu_assist/task/action/custom/` 下新建文件
3. 系统启动时自动发现并注册动作

### 新增知识意图

在 `edu_assist/engine/builder.py` 的 `build_dialogue_engine()` 中添加：
```python
provider_registry.register_intent(
    "intent_id",
    description="意图描述",
    provider_ids=["api.provider_id"],
)
```

### 新增自定义动作

```python
from edu_assist.task.action.base import Action, ActionResult

class MyAction(Action):
    name = "action_my_action"

    async def run(self, state, action_kwargs):
        # 执行逻辑
        return ActionResult(messages=[...], slot_updates={...})
```
