"""Action 执行器。"""

from __future__ import annotations

from typing import Any

from edu_assist.task.action.base import ActionCall, ActionResult
from edu_assist.task.action.registry import ActionRegistry
from edu_assist.task.action.builtin.listen import ActionListen
from edu_assist.task.action.builtin.response import ActionResponse


class ActionRunner:
    """动作执行器。"""

    def __init__(self, registry: ActionRegistry) -> None:
        self._registry = registry

    async def run(self, call: ActionCall, state: Any, slots: dict[str, Any]) -> ActionResult:
        """执行动作调用。"""
        action = self._registry.get(call.action_name)
        if action is None:
            return ActionResult(messages=[], slot_updates={})
        return await action.run(state, call.args)
