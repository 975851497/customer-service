"""创建退款申请动作。"""

from __future__ import annotations

from typing import Any

from edu_assist.task.action.base import Action, ActionResult
from edu_assist.domain.messages import BotMessage
from edu_assist.task.action.custom.shared import (create_refund_request)


REFUND_TYPE_MAP = {
    "personal_reason": "个人原因",
    "course_unsatisfied": "对课程不满意",
    "schedule_conflict": "时间冲突",
    "duplicate_purchase": "重复购买",
}


class CreateRefundAction(Action):
    """创建退款申请。"""
    name = "action_create_refund"

    async def run(self, state: Any, action_kwargs: dict[str, Any]) -> ActionResult:
        order_number = action_kwargs.get("order_number", "")
        reason = action_kwargs.get("refund_reason", "")
        refund_type = action_kwargs.get("refund_type", "personal_reason")

        if not order_number or not reason:
            return ActionResult(
                messages=[BotMessage(text="请提供订单号和退款原因。")]
            )

        user_id = self._extract_user_id(state.sender_id)

        # 简化处理：使用订单号作为 order_item_id（实际应该查订单获取）
        try:
            order_item_id = int(order_number) if order_number.isdigit() else 0
            result = await create_refund_request(
                order_item_id=order_item_id,
                refund_type=refund_type,
                refund_reason=reason,
                apply_amount=0,  # 简化处理
                user_id=user_id,
            )

            if result:
                refund_no = result.get("refundNo", "")
                status = result.get("refundStatusCode", "pending")
                msg = (
                    f"退款申请已提交！\n"
                    f"退款编号：{refund_no}\n"
                    f"当前状态：{status}\n"
                    f"退款原因：{reason}\n\n"
                    f"我们会尽快处理你的退款申请，请耐心等待。"
                )
                return ActionResult(messages=[BotMessage(text=msg)])
        except Exception:
            pass

        return ActionResult(
            messages=[BotMessage(text="退款申请提交失败，请稍后重试或联系人工客服处理。")]
        )

    def _extract_user_id(self, sender_id: str) -> int:
        parts = sender_id.split("_")
        if len(parts) > 1 and parts[-1].isdigit():
            return int(parts[-1])
        return 1
