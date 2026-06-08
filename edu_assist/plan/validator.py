"""回合规划验证器。"""

from __future__ import annotations

from enum import Enum

from edu_assist.plan.planner import TurnPlan


class ClarifyReason(str, Enum):
    """澄清原因枚举。"""
    MISSING_TRACK = "missing_track"
    MULTIPLE_TRACKS = "multiple_tracks"
    MISSING_TASK_COMMANDS = "missing_task_commands"
    MISSING_KNOWLEDGE_INTENT = "missing_knowledge_intent"
    MISSING_FOCUSED_OBJECT = "missing_focused_object"
    OBJECT_REQUIRES_INTENT = "object_requires_intent"


class TurnPlanValidator:
    """回合规划验证器。"""

    def validate(self, plan: TurnPlan, has_focused_object: bool = False) -> ClarifyReason | None:
        """验证规划结果，返回 None 表示有效，否则返回澄清原因。"""
        tracks = 0
        if plan.task is not None:
            tracks += 1
        if plan.knowledge is not None:
            tracks += 1
        if plan.chitchat is not None:
            tracks += 1

        if tracks == 0:
            return ClarifyReason.MISSING_TRACK
        if tracks > 1:
            return ClarifyReason.MULTIPLE_TRACKS

        if plan.task is not None and not plan.task.commands:
            return ClarifyReason.MISSING_TASK_COMMANDS

        if plan.knowledge is not None and not plan.knowledge.intents:
            return ClarifyReason.MISSING_KNOWLEDGE_INTENT

        return None
