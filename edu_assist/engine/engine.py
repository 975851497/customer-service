"""对话引擎。"""

from __future__ import annotations

from datetime import datetime

from edu_assist.domain.messages import BotMessage, MessageType, ProcessResult, UserMessage
from edu_assist.domain.state import DialogueState, SYSTEM_COLLECT_INFORMATION
from edu_assist.plan.planner import TurnPlanner
from edu_assist.plan.validator import TurnPlanValidator
from edu_assist.clarify.handler import ClarifyResponder
from edu_assist.chitchat.handler import ChitchatHandler
from edu_assist.knowledge.handler import KnowledgeHandler
from edu_assist.task.handler import TaskHandler

IDLE_TIMEOUT = 3600  # 1 小时


class DialogueEngine:
    """对话引擎，处理消息分发与响应生成。"""

    def __init__(
        self,
        turn_planner: TurnPlanner,
        turn_validator: TurnPlanValidator,
        task_handler: TaskHandler,
        knowledge_handler: KnowledgeHandler,
        chitchat_handler: ChitchatHandler,
        clarify_responder: ClarifyResponder,
    ) -> None:
        self._turn_planner = turn_planner
        self._turn_validator = turn_validator
        self._task_handler = task_handler
        self._knowledge_handler = knowledge_handler
        self._chitchat_handler = chitchat_handler
        self._clarify_responder = clarify_responder

    async def process_message(self, state: DialogueState, user_message: UserMessage) -> ProcessResult:
        """处理用户消息。"""
        # 1. 会话管理
        self._prepare_session(state)

        # 2. 开始新回合
        state.begin_turn(user_message)

        # 3. 消息类型判断
        if user_message.type == MessageType.OBJECT and user_message.object:
            bot_messages = await self._handle_object_message(state, user_message)
        else:
            bot_messages = await self._handle_text_message(state, user_message)

        # 4. 提交回合（保存对话历史）
        if state.pending_turn:
            state.pending_turn.bot_messages = bot_messages
        state.commit_pending_turn()

        return ProcessResult(
            sender_id=state.sender_id,
            messages=bot_messages,
        )

    def _prepare_session(self, state: DialogueState) -> None:
        """会话管理。"""
        now = datetime.now()
        if state.current_session is None:
            state.start_session()
        else:
            idle_seconds = (now - state.current_session.last_activity_at).total_seconds()
            if idle_seconds > IDLE_TIMEOUT:
                state.close_current_session()
                state.reset_runtime_state_for_new_session()
                state.start_session()

    async def _handle_object_message(self, state: DialogueState, user_message: UserMessage) -> list[BotMessage]:
        """处理对象消息（跳过 Turn Planner）。"""
        obj = user_message.object
        if obj is None:
            return []

        state.set_focused_object(obj)

        # 如果在收集流程中，自动填充 slot
        if state.active_system_task and state.active_system_task.flow_id == SYSTEM_COLLECT_INFORMATION:
            slot_name = state.active_system_task.context.get("slot_name", "")
            if obj.type == "order" and slot_name == "order_number":
                state.set_slots({"order_number": obj.id})
            elif obj.type == "cohort" and slot_name in ("cohort_id", "cohort_name"):
                state.set_slots({slot_name: obj.id})
            elif obj.type == "series" and slot_name == "series_name":
                state.set_slots({"series_name": obj.id})

            state.end_system_task()
            messages = await self._task_handler.handle([], state)

            # 如果有消息，替换占位的 collect 消息
            if messages:
                return messages

        # 默认的引导消息
        return [BotMessage(text=f"已收到{obj.type}信息：{obj.title or obj.id}。请问你想对它进行什么操作？")]

    async def _handle_text_message(self, state: DialogueState, user_message: UserMessage) -> list[BotMessage]:
        """处理文本消息。"""
        text = user_message.text or ""

        # 1. Turn Planning
        plan = await self._turn_planner.predict(state, text)

        # 调试日志
        plan_dict = plan.model_dump(exclude_none=True)
        print(f"\n=== TURN PLAN ===")
        print(f"User: {text}")
        import json
        print(json.dumps(plan_dict, ensure_ascii=False))
        print(f"================\n")

        # 2. 验证
        reason = self._turn_validator.validate(plan, has_focused_object=state.focused_object is not None)
        if reason:
            print(f"=== CLARIFY: {reason} ===")
            return await self._clarify_responder.respond(reason)

        # 3. 按赛道分发
        if plan.task:
            return await self._task_handler.handle(plan.task.commands, state)

        if plan.knowledge:
            return await self._knowledge_handler.handle(plan.knowledge.intents, state, text)

        if plan.chitchat:
            return await self._chitchat_handler.handle(state, text)

        # 兜底：闲聊
        return await self._chitchat_handler.handle(state, text)
