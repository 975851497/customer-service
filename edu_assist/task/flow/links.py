"""流程步骤链接定义。"""

from __future__ import annotations

from typing import Any


class StepLink:
    """步骤链接。"""
    pass


class StaticLink(StepLink):
    """静态跳转。"""
    def __init__(self, target: str) -> None:
        self.target = target


class ConditionalLink(StepLink):
    """条件跳转。"""
    def __init__(self, condition: str, target: str) -> None:
        self.condition = condition
        self.target = target


class FallbackLink(StepLink):
    """兜底跳转。"""
    def __init__(self, target: str) -> None:
        self.target = target


def parse_next(next_def: str | list[Any]) -> list[StepLink]:
    """解析 next 字段为链接列表。"""
    if isinstance(next_def, str):
        return [StaticLink(next_def)]
    links: list[StepLink] = []
    for item in next_def:
        if isinstance(item, dict):
            if "if" in item:
                links.append(ConditionalLink(item["if"], item["then"]))
            elif "else" in item:
                links.append(FallbackLink(item["else"]))
    return links


def evaluate_links(links: list[StepLink], slots: dict[str, Any], context: dict[str, Any] | None = None) -> str | None:
    """评估链接列表，返回第一个匹配的目标步骤 ID。"""
    ctx = context or {}
    for link in links:
        if isinstance(link, StaticLink):
            return link.target
        if isinstance(link, ConditionalLink):
            try:
                if eval(link.condition, {"slots": slots, "context": ctx}):
                    return link.target
            except Exception:
                continue
        if isinstance(link, FallbackLink):
            return link.target
    return None
