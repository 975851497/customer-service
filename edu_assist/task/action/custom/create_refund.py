"""创建退款申请动作。"""

from __future__ import annotations

from typing import Any

from edu_assist.task.action.base import Action, ActionResult
from edu_assist.domain.messages import BotMessage
from edu_assist.task.action.custom.shared import create_refund_request, fetch_my_orders


REFUND_TYPE_MAP = {
    "personal_reason": "个人原因",
    "course_unsatisfied": "对课程不满意",
    "schedule_conflict": "时间冲突",
    "duplicate_purchase": "重复购买",
}

# 反向映射：中文描述 → 代码值
_REFUND_TYPE_REVERSE = {v: k for k, v in REFUND_TYPE_MAP.items()}


def _normalize_refund_type(refund_type: str) -> str:
    """将退款类型统一为代码值。"""
    if refund_type in REFUND_TYPE_MAP:
        return refund_type  # 已经是代码值
    return _REFUND_TYPE_REVERSE.get(refund_type, "personal_reason")


class CreateRefundAction(Action):
    """创建退款申请。"""
    name = "action_create_refund"

    async def run(self, state: Any, action_kwargs: dict[str, Any]) -> ActionResult:
        order_number = action_kwargs.get("order_number", "")
        reason = action_kwargs.get("refund_reason", "")
        refund_type = _normalize_refund_type(action_kwargs.get("refund_type", "personal_reason"))

        if not order_number or not reason:
            return ActionResult(
                messages=[BotMessage(text="请提供订单号和退款原因。")]
            )

        user_id = self._extract_user_id(state.sender_id)

        try:
            # 先查用户订单列表，找到匹配的 orderItemId
            orders = await fetch_my_orders(user_id)
            order_item_id = None
            matched_order = None

            for order in orders:
                if order_number in order.get("orderNo", ""):
                    matched_order = order
                    items = order.get("orderItems", [])
                    if items:
                        order_item_id = items[0].get("orderItemId")
                    break

            if not order_item_id:
                return ActionResult(
                    messages=[BotMessage(text=f"未找到订单 {order_number}，请确认订单号是否正确。")]
                )

            result = await create_refund_request(
                order_item_id=order_item_id,
                refund_type=refund_type,
                refund_reason=reason,
                apply_amount=matched_order.get("payableAmount", 0) if matched_order else 0,
                user_id=user_id,
            )

            if result:
                msg = (
                    f"退款申请已提交！\n"
                    f"退款编号：{result.get('refundRequestId', '')}\n"
                    f"退款类型：{REFUND_TYPE_MAP.get(refund_type, refund_type)}\n"
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
        if sender_id.isdigit():
            return int(sender_id)
        return 1
