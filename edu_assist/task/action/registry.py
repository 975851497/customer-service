"""Action 注册表。"""

from __future__ import annotations

from edu_assist.task.action.base import Action


class ActionRegistry:
    """动作注册表。"""

    def __init__(self) -> None:
        self._actions: dict[str, Action] = {}

    def register(self, action: Action) -> None:
        """注册动作。"""
        self._actions[action.name] = action

    def get(self, name: str) -> Action | None:
        """获取动作。"""
        return self._actions.get(name)
