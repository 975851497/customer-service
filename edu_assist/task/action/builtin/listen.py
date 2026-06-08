"""action_listen: 等待用户输入。"""

from __future__ import annotations

from typing import Any

from edu_assist.task.action.base import Action, ActionResult


class ActionListen(Action):
    """等待用户输入（暂停流程）。"""
    name = "action_listen"

    async def run(self, state: Any, action_kwargs: dict[str, Any]) -> ActionResult:
        return ActionResult()
