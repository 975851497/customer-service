"""对话服务层。"""

from __future__ import annotations

from edu_assist.domain.messages import UserMessage
from edu_assist.domain.state import DialogueState
from edu_assist.engine.engine import DialogueEngine
from edu_assist.repository.state_repository import DialogueStateRepository


class DialogueService:
    """对话服务，编排对话处理的完整事务。"""

    def __init__(self, engine: DialogueEngine, repository: DialogueStateRepository) -> None:
        self._engine = engine
        self._repository = repository

    async def process_message(self, sender_id: str, user_message: UserMessage) -> dict:
        """处理消息。"""
        # 加载状态
        state = await self._repository.load_state(sender_id)

        # 引擎处理
        result = await self._engine.process_message(state, user_message)

        # 持久化
        await self._repository.save_state(state)

        return result.model_dump()

    async def get_history(self, sender_id: str) -> dict:
        """获取聊天历史。"""
        state = await self._repository.load_state(sender_id)
        messages = []
        if state.current_session:
            for turn in state.current_session.turns:
                user_msg = turn.user_message
                messages.append({
                    "role": "user",
                    "text": user_msg.text,
                    "object": user_msg.object.model_dump() if user_msg.object else None,
                })
                for bot_msg in turn.bot_messages:
                    messages.append({
                        "role": "bot",
                        "text": bot_msg.text,
                        "object": bot_msg.object.model_dump() if bot_msg.object else None,
                    })
        return {"sender_id": sender_id, "messages": messages}

    async def get_session_state(self, sender_id: str) -> dict:
        """获取当前会话状态。"""
        state = await self._repository.load_state(sender_id)
        return {
            "sender_id": sender_id,
            "session_id": state.current_session_id,
            "has_active_task": state.active_task is not None,
            "active_task_flow_id": state.active_task.flow_id if state.active_task else None,
            "active_task_name": state.active_task.name if state.active_task else None,
            "active_task_slots": state.active_task.slots if state.active_task else {},
            "paused_task_count": len(state.paused_tasks),
            "paused_tasks": [{"flow_id": t.flow_id, "name": t.name} for t in state.paused_tasks],
        }
