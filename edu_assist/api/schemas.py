"""API 请求/响应 Schema。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatObject(BaseModel):
    """结构化对象 Schema。"""
    type: str
    id: str
    title: str | None = None
    attributes: dict[str, Any] = {}


class ChatRequest(BaseModel):
    """聊天请求。"""
    sender_id: str
    message_id: str | None = None
    text: str | None = None
    object: ChatObject | None = None


class ChatBotMessage(BaseModel):
    """机器人回复消息 Schema。"""
    text: str | None = None
    object: ChatObject | None = None


class ChatResponse(BaseModel):
    """聊天响应。"""
    sender_id: str
    message_id: str
    messages: list[ChatBotMessage]


class HistoryMessage(BaseModel):
    """历史消息。"""
    role: str  # "user" | "bot"
    text: str | None = None
    object: ChatObject | None = None


class HistoryResponse(BaseModel):
    """历史响应。"""
    sender_id: str
    messages: list[HistoryMessage]


class SessionStateResponse(BaseModel):
    """会话状态响应。"""
    sender_id: str
    session_id: str
    has_active_task: bool
    active_task_flow_id: str | None = None
    active_task_name: str | None = None
    slots: dict[str, Any] = {}
    paused_task_count: int = 0
