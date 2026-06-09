"""action_response: 生成回复。"""

from __future__ import annotations

from typing import Any

from jinja2 import Template
from langchain_core.messages import HumanMessage, SystemMessage

from edu_assist.task.action.base import Action, ActionResult
from edu_assist.domain.messages import BotMessage
from edu_assist.infrastructure.llm import get_llm


class ActionResponse(Action):
    """生成回复动作，支持 static / rephrase / llm 三种模式。"""
    name = "action_response"

    async def run(self, state: Any, action_kwargs: dict[str, Any]) -> ActionResult:
        mode = action_kwargs.get("mode", "static")
        text = action_kwargs.get("text", "")
        prompt_template = action_kwargs.get("prompt", "")

        if mode == "static":
            return ActionResult(messages=[BotMessage(text=text)])

        elif mode == "rephrase":
            current_response = text
            if prompt_template:
                system_prompt = Template(prompt_template).render()
                llm = get_llm()
                try:
                    result = await llm.ainvoke([
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=current_response),
                    ])
                    return ActionResult(messages=[BotMessage(text=result.content)])
                except Exception:
                    return ActionResult(messages=[BotMessage(text=current_response)])
            return ActionResult(messages=[BotMessage(text=current_response)])

        elif mode == "llm":
            if prompt_template:
                history_text = self._build_history(state)
                user_msg = ""
                if state.pending_turn and state.pending_turn.user_message:
                    user_msg = state.pending_turn.user_message.text or ""
                rendered = Template(prompt_template).render(
                    history=history_text,
                    user_message=user_msg,
                )
                try:
                    result = await llm_ainvoke(rendered)
                    return ActionResult(messages=[BotMessage(text=result)])
                except Exception:
                    return ActionResult(messages=[BotMessage(text="抱歉，我暂时无法处理你的请求。")])

        return ActionResult(messages=[BotMessage(text=text)])

    def _build_history(self, state: Any) -> str:
        """构建对话历史文本。"""
        lines = []
        if state.current_session:
            for turn in state.current_session.turns[-10:]:
                user_msg = turn.user_message
                if user_msg.text:
                    lines.append(f"USER: {user_msg.text}")
                elif user_msg.object:
                    obj = user_msg.object
                    lines.append(f"USER: [{obj.type} id={obj.id}, title={obj.title}]")
                for bot_msg in turn.bot_messages:
                    if bot_msg.text:
                        lines.append(f"BOT: {bot_msg.text}")
        return "\n".join(lines)
