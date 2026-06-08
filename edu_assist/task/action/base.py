"""Action 抽象基类和 ActionCall。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from edu_assist.domain.messages import BotMessage


@dataclass
class ActionResult:
    """动作执行结果。"""
    messages: list[BotMessage] = field(default_factory=list)
    slot_updates: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionCall:
    """动作调用。"""
    action_name: str
    args: dict[str, Any]
    next_step_id: str


class Action(ABC):
    """动作抽象基类。"""
    name: str = ""

    @abstractmethod
    async def run(self, state: Any, action_kwargs: dict[str, Any]) -> ActionResult:
        """执行动作。"""
        ...
