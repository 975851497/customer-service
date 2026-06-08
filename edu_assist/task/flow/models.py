"""流程数据模型。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class FlowSlot(BaseModel):
    """流程 Slot 定义。"""
    name: str
    type: str = "text"
    label: str = ""
    description: str = ""


class Flow(BaseModel):
    """流程定义。"""
    id: str
    name: str
    description: str = ""
    steps: list[dict[str, Any]] = []
    slots: list[FlowSlot] = []


class FlowsList(BaseModel):
    """流程列表容器。"""
    flows: dict[str, Flow] = {}
    slots: dict[str, Any] = {}
