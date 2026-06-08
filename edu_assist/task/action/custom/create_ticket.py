"""创建工单动作。"""

from __future__ import annotations

from typing import Any

from edu_assist.task.action.base import Action, ActionResult
from edu_assist.domain.messages import BotMessage
from edu_assist.task.action.custom.shared import create_service_ticket


TICKET_TYPE_MAP = {
    "after_sales": "售后",
    "complaint": "投诉",
    "refund": "退款",
}


class CreateTicketAction(Action):
    """创建工单。"""
    name = "action_create_ticket"

    async def run(self, state: Any, action_kwargs: dict[str, Any]) -> ActionResult:
        ticket_type = action_kwargs.get("ticket_type", "after_sales")
        description = action_kwargs.get("description", "")
        order_number = action_kwargs.get("order_number", "")

        if not description:
            return ActionResult(
                messages=[BotMessage(text="请描述你遇到的问题，以便我们创建工单。")]
            )

        user_id = self._extract_user_id(state.sender_id)
        ticket_type_name = TICKET_TYPE_MAP.get(ticket_type, ticket_type)

        try:
            order_item_id = int(order_number) if order_number and order_number.isdigit() else 0
            result = await create_service_ticket(
                ticket_type=ticket_type,
                title=f"【{ticket_type_name}】{description[:50]}",
                content=description,
                student_id=1,  # 简化处理
                order_item_id=order_item_id if order_item_id > 0 else 1,
                user_id=user_id,
            )

            if result:
                ticket_no = result.get("ticketNo", "")
                ticket_id = result.get("ticketId", "")
                msg = (
                    f"工单已提交成功！\n"
                    f"工单编号：{ticket_no}\n"
                    f"工单类型：{ticket_type_name}\n"
                    f"问题描述：{description}\n\n"
                    f"我们会尽快处理你的工单，请耐心等待。工单编号可用于查询处理进度。"
                )
                return ActionResult(messages=[BotMessage(text=msg)])
        except Exception:
            pass

        return ActionResult(
            messages=[BotMessage(text="工单提交失败，请稍后重试或联系人工客服处理。")]
        )

    def _extract_user_id(self, sender_id: str) -> int:
        parts = sender_id.split("_")
        if len(parts) > 1 and parts[-1].isdigit():
            return int(parts[-1])
        return 1
