"""命令处理。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from edu_assist.domain.state import DialogueState, SYSTEM_TASK_CANCELED, SYSTEM_TASK_RESUMED, SYSTEM_TASK_STARTED


@dataclass
class Command:
    """命令基类。"""
    pass


@dataclass
class StartFlowCommand(Command):
    """启动流程命令。"""
    flow_id: str
    flow_name: str = ""


@dataclass
class SetSlotsCommand(Command):
    """设置 Slot 命令。"""
    slots: dict[str, Any]


@dataclass
class CancelFlowCommand(Command):
    """取消流程命令。"""
    pass


@dataclass
class ResumeFlowCommand(Command):
    """恢复流程命令。"""
    flow_id: str


class CommandProcessor:
    """命令处理器。"""

    async def run(self, commands: list[dict[str, Any]], state: DialogueState) -> None:
        """执行命令列表。"""
        for cmd_dict in commands:
            cmd = self._parse_command(cmd_dict)
            if isinstance(cmd, StartFlowCommand):
                if state.active_task:
                    state.interrupt_active_task()
                state.start_task(cmd.flow_id, cmd.flow_name)
                state.start_system_task(SYSTEM_TASK_STARTED, {"name": cmd.flow_name})

            elif isinstance(cmd, SetSlotsCommand):
                state.set_slots(cmd.slots)

            elif isinstance(cmd, CancelFlowCommand):
                state.cancel_active_task()
                state.start_system_task(SYSTEM_TASK_CANCELED)

            elif isinstance(cmd, ResumeFlowCommand):
                if state.active_task and state.active_task.flow_id != cmd.flow_id:
                    state.interrupt_active_task()
                if state.resume_task(cmd.flow_id):
                    state.start_system_task(SYSTEM_TASK_RESUMED)

    def _parse_command(self, cmd_dict: dict[str, Any]) -> Command:
        cmd_type = cmd_dict.get("type", "")
        if cmd_type == "start_flow":
            return StartFlowCommand(
                flow_id=cmd_dict.get("flow_id", ""),
                flow_name=cmd_dict.get("flow_name", ""),
            )
        elif cmd_type == "set_slots":
            return SetSlotsCommand(slots=cmd_dict.get("slots", {}))
        elif cmd_type == "cancel_flow":
            return CancelFlowCommand()
        elif cmd_type == "resume_flow":
            return ResumeFlowCommand(flow_id=cmd_dict.get("flow_id", ""))
        return Command()
