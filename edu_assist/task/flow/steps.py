"""流程步骤定义。"""

from __future__ import annotations

from typing import Any
from enum import Enum


class StepType(str, Enum):
    """步骤类型枚举。"""
    START = "start"
    ACTION = "action"
    COLLECT = "collect"
    END = "end"
