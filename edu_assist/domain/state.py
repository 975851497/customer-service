"""对话状态管理（领域层）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from edu_assist.domain.messages import MessageObject, Session, Turn, UserMessage

# 系统流程 ID 常量
SYSTEM_TASK_STARTED = "system_task_started"
SYSTEM_TASK_INTERRUPTED = "system_task_interrupted"
SYSTEM_TASK_CANCELED = "system_task_canceled"
SYSTEM_TASK_RESUMED = "system_task_resumed"
SYSTEM_COLLECT_INFORMATION = "system_collect_information"
SYSTEM_CANNOT_HANDLE = "system_cannot_handle"
SYSTEM_COMPLETED = "system_completed"


class TaskContext(BaseModel):
    """用户任务上下文。"""
    flow_id: str
    step_id: str
    slots: dict[str, Any] = {}
    name: str = ""


class SystemContext(BaseModel):
    """系统任务上下文。"""
    flow_id: str
    step_id: str
    context: dict[str, Any] = {}


class DialogueState(BaseModel):
    """对话状态聚合根。"""
    sender_id: str
    active_task: TaskContext | None = None
    paused_tasks: list[TaskContext] = []
    active_system_task: SystemContext | None = None
    focused_object: MessageObject | None = None
    sessions: list[Session] = []
    current_session_id: str | None = None
    pending_turn: Turn | None = None

    @property
    def current_session(self) -> Session | None:
        if self.current_session_id is None:
            return None
        for s in self.sessions:
            if s.session_id == self.current_session_id:
                return s
        return None

    def start_session(self) -> None:
        session = Session()
        self.sessions.append(session)
        self.current_session_id = session.session_id

    def close_current_session(self) -> None:
        if self.current_session:
            self.current_session.closed_at = datetime.now()

    def reset_runtime_state_for_new_session(self) -> None:
        self.active_task = None
        self.paused_tasks = []
        self.active_system_task = None
        self.focused_object = None
        self.pending_turn = None

    def begin_turn(self, user_message: UserMessage) -> Turn:
        turn = Turn(user_message=user_message)
        self.pending_turn = turn
        return turn

    def commit_pending_turn(self) -> None:
        if self.pending_turn and self.current_session:
            self.current_session.turns.append(self.pending_turn)
            self.current_session.last_activity_at = datetime.now()
        self.pending_turn = None

    def start_task(self, flow_id: str, name: str = "") -> TaskContext:
        task = TaskContext(flow_id=flow_id, step_id="start", name=name)
        self.active_task = task
        return task

    def end_active_task(self) -> None:
        self.active_task = None

    def interrupt_active_task(self) -> None:
        if self.active_task:
            self.paused_tasks.append(self.active_task)
            self.active_task = None

    def resume_task(self, flow_id: str) -> bool:
        for i, task in enumerate(self.paused_tasks):
            if task.flow_id == flow_id:
                self.active_task = self.paused_tasks.pop(i)
                return True
        return False

    def cancel_active_task(self) -> None:
        self.active_task = None

    def set_slots(self, slots: dict[str, Any]) -> None:
        if self.active_task:
            self.active_task.slots.update(slots)

    def remove_slot(self, name: str) -> None:
        if self.active_task and name in self.active_task.slots:
            del self.active_task.slots[name]

    def start_system_task(self, flow_id: str, context: dict[str, Any] | None = None) -> SystemContext:
        task = SystemContext(flow_id=flow_id, step_id="start", context=context or {})
        self.active_system_task = task
        return task

    def end_system_task(self) -> None:
        self.active_system_task = None

    def set_focused_object(self, obj: MessageObject) -> None:
        self.focused_object = obj
