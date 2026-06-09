"""任务处理器，处理 task 赛道的消息。"""

from __future__ import annotations

from typing import Any

from edu_assist.domain.messages import BotMessage
from edu_assist.domain.state import DialogueState
from edu_assist.task.command import CommandProcessor
from edu_assist.task.flow.executor import FlowExecutor


class TaskHandler:
    """任务处理器，处理 task 赛道的消息。"""

    def __init__(self, command_processor: CommandProcessor, flow_executor: FlowExecutor) -> None:
        self._command_processor = command_processor
        self._flow_executor = flow_executor

    async def handle(self, commands: list[dict[str, Any]], state: DialogueState) -> list[BotMessage]:
        """处理 task 命令并执行流程。"""
        await self._command_processor.run(commands, state)

        messages: list[BotMessage] = []

        # 先执行系统流程（如任务启动通知、信息收集等）
        if state.active_system_task:
            system_msgs = await self._flow_executor.run_task(state, task=state.active_system_task)
            messages.extend(system_msgs)

        # 再执行用户流程
        if state.active_task:
            task_msgs = await self._flow_executor.run_task(state, task=state.active_task)
            messages.extend(task_msgs)

        return messages
