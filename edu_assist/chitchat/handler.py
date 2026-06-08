"""闲聊处理器。"""

from __future__ import annotations

from edu_assist.domain.messages import BotMessage
from edu_assist.infrastructure.llm import llm_ainvoke
from edu_assist.prompts.prompt_loader import load_prompt
from edu_assist.prompts.history_builder import HistoryBuilder


class ChitchatHandler:
    """闲聊处理器。"""

    async def handle(self, state: Any, user_message_text: str) -> list[BotMessage]:
        """处理闲聊消息。"""
        try:
            history = HistoryBuilder.build(state)
            template = load_prompt("chitchat_respond.jinja2")
            prompt = template.render(
                history=history,
                user_message=user_message_text,
            )
            result = await llm_ainvoke(prompt)
            return [BotMessage(text=result)]
        except Exception:
            return [BotMessage(text="你好！我是教育智能客服助手，可以帮你查询课程信息、订单状态、学习进度等。请问有什么可以帮助你的？")]
