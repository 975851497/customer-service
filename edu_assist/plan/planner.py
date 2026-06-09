"""回合规划器。"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from edu_assist.infrastructure.llm import llm_ainvoke
from edu_assist.prompts.prompt_loader import load_prompt
from edu_assist.prompts.history_builder import HistoryBuilder
from edu_assist.domain.state import SYSTEM_COLLECT_INFORMATION


class TaskTurnPlan(BaseModel):
    """任务赛道规划。"""
    commands: list[dict[str, Any]] = []


class KnowledgeTurnPlan(BaseModel):
    """知识赛道规划。"""
    intents: list[str] = []


class ChitchatTurnPlan(BaseModel):
    """闲聊赛道规划。"""
    pass


class TurnPlan(BaseModel):
    """回合规划结果。"""
    task: TaskTurnPlan | None = None
    knowledge: KnowledgeTurnPlan | None = None
    chitchat: ChitchatTurnPlan | None = None


class TurnPlanner:
    """回合规划器。"""

    def __init__(self, available_flows: str, knowledge_intents: str) -> None:
        self._available_flows = available_flows
        self._knowledge_intents = knowledge_intents

    async def predict(
        self,
        state: Any,
        user_message_text: str,
    ) -> TurnPlan:
        """预测当前回合的规划。"""
        history = HistoryBuilder.build(state)
        active_task_info = ""
        interrupted_tasks_info = ""
        focused_object_info = ""

        if state.active_task:
            collecting = ""
            if state.active_system_task and state.active_system_task.flow_id == SYSTEM_COLLECT_INFORMATION:
                collecting = state.active_system_task.context.get("slot_name", "")
            active_task_info = json.dumps({
                "flow_id": state.active_task.flow_id,
                "name": state.active_task.name,
                "current_step": state.active_task.step_id,
                "slots": state.active_task.slots,
                "collecting_slot": collecting,
            }, ensure_ascii=False)

        if state.paused_tasks:
            paused = [{"flow_id": t.flow_id, "name": t.name} for t in state.paused_tasks]
            interrupted_tasks_info = json.dumps(paused, ensure_ascii=False)

        if state.focused_object:
            focused_object_info = json.dumps({
                "type": state.focused_object.type,
                "id": state.focused_object.id,
                "title": state.focused_object.title,
            }, ensure_ascii=False)

        try:
            template = load_prompt("turn_plan.jinja2")
            prompt = template.render(
                history=history,
                user_message=user_message_text,
                available_flows=self._available_flows,
                active_task=active_task_info,
                interrupted_tasks=interrupted_tasks_info,
                focused_object=focused_object_info,
                knowledge_intents=self._knowledge_intents,
            )
            result = await llm_ainvoke(prompt)
            # 尝试解析 JSON
            result = result.strip()
            if result.startswith("```"):
                result = result.split("\n", 1)[1].rsplit("\n", 1)[0]
            plan_data = json.loads(result)
            return TurnPlan.model_validate(plan_data)

        except Exception:
            # 解析失败，默认走闲聊
            return TurnPlan(chitchat=ChitchatTurnPlan())
