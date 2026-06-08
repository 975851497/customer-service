"""澄清处理器。"""

from __future__ import annotations

from edu_assist.domain.messages import BotMessage
from edu_assist.infrastructure.llm import llm_ainvoke
from edu_assist.prompts.prompt_loader import load_prompt
from edu_assist.plan.validator import ClarifyReason


CLARIFY_MESSAGES = {
    ClarifyReason.MISSING_TRACK: "我没太理解你的意思。你可以告诉我你想查课程、查订单、查学习进度，还是申请退款吗？",
    ClarifyReason.MULTIPLE_TRACKS: "我注意到你似乎想同时处理几件事。请先告诉我你最想先处理哪一个？",
    ClarifyReason.MISSING_TASK_COMMANDS: "你想处理什么类型的业务呢？比如查询订单、查看学习进度、申请退款或提交工单。",
    ClarifyReason.MISSING_KNOWLEDGE_INTENT: "你想了解关于课程的哪些信息？比如课程内容、价格、班次安排等。",
    ClarifyReason.MISSING_FOCUSED_OBJECT: "你需要先选择一个课程、班次或订单，我才能帮你查询相关信息。",
    ClarifyReason.OBJECT_REQUIRES_INTENT: "你发来的这个信息我看到了。你想对它进行什么操作呢？",
}


class ClarifyResponder:
    """澄清回复生成器。"""

    async def respond(self, reason: ClarifyReason) -> list[BotMessage]:
        """根据澄清原因生成回复。"""
        message = CLARIFY_MESSAGES.get(reason, "抱歉，我没有完全理解你的意思，请再详细描述一下。")
        try:
            template = load_prompt("clarify_respond.jinja2")
            prompt = template.render(clarify_message=message)
            result = await llm_ainvoke(prompt)
            return [BotMessage(text=result)]
        except Exception:
            return [BotMessage(text=message)]
