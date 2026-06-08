"""领域消息模型。"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """消息类型。"""
    TEXT = "text"
    OBJECT = "object"


class MessageObject(BaseModel):
    """结构化对象，如订单、班次等。"""
    type: str  # order, cohort, series, etc.
    id: str
    title: str | None = None
    attributes: dict[str, Any] = {}


class UserMessage(BaseModel):
    """用户消息。"""
    sender_id: str
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    type: MessageType = MessageType.TEXT
    text: str | None = None
    object: MessageObject | None = None


class BotMessage(BaseModel):
    """机器人回复消息。"""
    text: str | None = None
    object: MessageObject | None = None


class ProcessResult(BaseModel):
    """消息处理结果。"""
    sender_id: str
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    messages: list[BotMessage] = []


class Turn(BaseModel):
    """一个对话回合。"""
    turn_id: str = Field(default_factory=lambda: str(uuid4()))
    user_message: UserMessage
    bot_messages: list[BotMessage] = []
    created_at: datetime = Field(default_factory=datetime.now)


class Session(BaseModel):
    """一次对话会话。"""
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    started_at: datetime = Field(default_factory=datetime.now)
    last_activity_at: datetime = Field(default_factory=datetime.now)
    closed_at: datetime | None = None
    turns: list[Turn] = []
