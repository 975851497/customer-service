# API 接口参考

## 基础信息

| 项目 | 说明 |
|------|------|
| 基础路径 | `http://{host}:{port}` |
| 默认端口 | `18082` |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |

---

## 1. 发送对话消息

`POST /api/chat`

发送用户消息并获取机器人回复。

### 请求

**请求体 (ChatRequest)**

```json
{
  "sender_id": "user_001",
  "message_id": "msg_uuid_optional",
  "text": "帮我查一下订单123456的状态",
  "object": null
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sender_id` | `string` | 是 | 发送者唯一标识 |
| `message_id` | `string` | 否 | 消息 ID，不传则自动生成 UUID |
| `text` | `string` | 否 | 文本消息内容（文本消息时必填） |
| `object` | `object` | 否 | 结构化对象消息（对象消息时必填） |

### 对象消息格式

当用户通过点击卡片等方式发送结构化对象时：

```json
{
  "sender_id": "user_001",
  "object": {
    "type": "order",
    "id": "123456",
    "title": "订单 #123456",
    "attributes": {
      "amount": "299.00",
      "status": "已发货"
    }
  }
}
```

**支持的对象类型**：

| 对象类型 | 说明 | 自动映射 |
|---------|------|----------|
| `order` | 订单对象 | `order_number` slot |
| `product` | 商品对象 | `product_id` slot |

### 响应

**正常响应 (ChatResponse)**

```json
{
  "sender_id": "user_001",
  "message_id": "resp_uuid",
  "messages": [
    {
      "text": "订单123456当前状态是：已发货。订单金额299.00元，由顺丰速运配送。",
      "object": null
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `sender_id` | `string` | 发送者 ID（与请求一致） |
| `message_id` | `string` | 响应消息 ID |
| `messages` | `array` | 机器人回复消息列表 |

**消息对象 (ChatBotMessage)**

| 字段 | 类型 | 说明 |
|------|------|------|
| `text` | `string` | 文本内容 |
| `object` | `object` | 结构化对象（如商品卡片） |

### 错误情况

| 状态码 | 说明 |
|--------|------|
| `422` | 请求参数校验失败 |
| `500` | 服务器内部错误 |

---

## 2. 获取聊天历史

`GET /api/chat/history?sender_id={sender_id}`

获取指定用户的聊天历史。

> **注意**：当前为占位实现，返回硬编码的测试数据。完整功能待后续开发。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sender_id` | `string` | 是 | 用户标识 |

### 响应 (HistoryResponse)

```json
{
  "sender_id": "user_001",
  "messages": [
    {
      "role": "user",
      "text": "你好",
      "object": null
    },
    {
      "role": "bot",
      "text": "我不好",
      "object": null
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `sender_id` | `string` | 用户标识 |
| `messages` | `array` | 历史消息列表 |

**历史消息 (HistoryMessage)**

| 字段 | 类型 | 说明 |
|------|------|------|
| `role` | `string` | 角色：`user` 或 `bot` |
| `text` | `string` | 消息文本 |
| `object` | `object` | 结构化对象 |

## 请求示例

### cURL

```bash
# 文本消息查询订单状态
curl -X POST "http://127.0.0.1:18082/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": "user_001",
    "text": "帮我查一下订单123456的状态"
  }'

# 发送对象消息（点击订单卡片）
curl -X POST "http://127.0.0.1:18082/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": "user_001",
    "object": {
      "type": "order",
      "id": "123456",
      "title": "订单 #123456"
    }
  }'

# 闲聊消息
curl -X POST "http://127.0.0.1:18082/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": "user_001",
    "text": "你好，今天天气真不错"
  }'
```

### Python (httpx)

```python
import httpx

client = httpx.Client(base_url="http://127.0.0.1:18082")

# 发送消息
response = client.post("/api/chat", json={
    "sender_id": "user_001",
    "text": "帮我查一下订单123456的状态"
})
print(response.json())

# 获取历史
history = client.get("/api/chat/history", params={"sender_id": "user_001"})
print(history.json())
```

## 请求/响应 Schema（源码定义）

参见 `atguigu/api/schemas.py`：

```python
class ChatObject(BaseModel):
    type: str
    id: str
    title: str | None = None
    attributes: dict = {}

class ChatRequest(BaseModel):
    sender_id: str
    message_id: str | None = None
    text: str | None = None
    object: ChatObject | None = None

class ChatBotMessage(BaseModel):
    text: str | None = None
    object: ChatObject | None = None

class ChatResponse(BaseModel):
    sender_id: str
    message_id: str
    messages: list[ChatBotMessage]
```
