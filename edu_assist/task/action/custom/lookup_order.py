"""查询订单状态动作。"""

from __future__ import annotations

from typing import Any

from edu_assist.task.action.base import Action, ActionResult
from edu_assist.domain.messages import BotMessage
from edu_assist.task.action.custom.shared import fetch_order_detail


STATUS_MAP = {
    "pending": "待支付",
    "paid": "已支付",
    "completed": "已完成",
    "cancelled": "已取消",
    "partial_refunded": "部分退款",
    "refunded": "已退款",
}


class LookupOrderAction(Action):
    """查询订单信息。"""
    name = "action_lookup_order"

    async def run(self, state: Any, action_kwargs: dict[str, Any]) -> ActionResult:
        order_number = action_kwargs.get("order_number", "")

        # 尝试从 slots 获取
        if not order_number and state.active_task:
            order_number = state.active_task.slots.get("order_number", "")

        if not order_number:
            return ActionResult(
                messages=[BotMessage(text="请提供订单号。")],
            )

        # 尝试从 sender_id 解析 user_id
        user_id = self._extract_user_id(state.sender_id)

        try:
            order_id = int(order_number) if order_number.isdigit() else 0
            detail = await fetch_order_detail(order_id, user_id) if order_id > 0 else None
            if detail:
                status = STATUS_MAP.get(detail.get("orderStatusCode", ""), detail.get("orderStatusCode", ""))
                items = detail.get("orderItems", [])
                item_info = ""
                if items:
                    item = items[0]
                    item_info = f"报名课程：{item.get('seriesName', '')} - {item.get('cohortName', '')}"

                payment = detail.get("paymentSummary", {})
                paid_info = ""
                if payment.get("paymentStatusCode") == "paid":
                    paid_info = f"支付时间：{payment.get('paidAt', '')}"

                msg = (
                    f"订单号：{detail.get('orderNo', '')}\n"
                    f"订单状态：{status}\n"
                    f"{item_info}\n"
                    f"应付金额：{detail.get('payableAmount', 0)}元\n"
                    f"实付金额：{detail.get('paidAmount', 0)}元\n"
                    f"{paid_info}"
                )
                return ActionResult(
                    messages=[BotMessage(text=msg)],
                    slot_updates={"order_status": detail.get("orderStatusCode", "")},
                )
        except (ValueError, TypeError):
            pass

        return ActionResult(
            messages=[BotMessage(text=f"未找到订单 {order_number} 的信息。请确认订单号是否正确。")]
        )

    def _extract_user_id(self, sender_id: str) -> int:
        """从 sender_id 提取用户 ID。"""
        # sender_id 格式如 "user_1"，提取数字部分
        parts = sender_id.split("_")
        if len(parts) > 1 and parts[-1].isdigit():
            return int(parts[-1])
        return 1  # 默认用户
