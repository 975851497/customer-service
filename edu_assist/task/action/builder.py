"""Action 发现与注册构建器。"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

from edu_assist.task.action.base import Action
from edu_assist.task.action.builtin.listen import ActionListen
from edu_assist.task.action.builtin.response import ActionResponse
from edu_assist.task.action.registry import ActionRegistry


def register_builtin_actions(registry: ActionRegistry) -> None:
    """注册内置动作。"""
    registry.register(ActionListen())
    registry.register(ActionResponse())


def register_custom_actions(registry: ActionRegistry) -> None:
    """自动发现并注册自定义动作。"""
    package = importlib.import_module("edu_assist.task.action.custom")
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"edu_assist.task.action.custom.{module_name}")
        for _, obj in inspect.getmembers(
            module,
            lambda o: isinstance(o, type) and issubclass(o, Action) and o is not Action,
        ):
            registry.register(obj())
