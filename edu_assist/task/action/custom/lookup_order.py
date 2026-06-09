"""查询订单状态动作。"""

from __future__ import annotations

from typing import Any

from edu_assist.task.action.base import Action, ActionResult
from edu_assist.domain.messages import BotMessage
from edu_assist.task.action.custom.shared import fetch_order_detail, fetch_my_orders


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

        # 从 sender_id 解析 user_id
        user_id = self._extract_user_id(state.sender_id)
        print(f"\n[LookupOrder] order_number='{order_number}', user_id={user_id}")

        # 策略 1：如果输入纯数字，尝试直接作为 orderId 查询
        if order_number.isdigit():
            try:
                detail = await fetch_order_detail(int(order_number), user_id)
                if detail:
                    return self._build_response(detail)
            except Exception:
                pass

        # 策略 2：获取用户的订单列表，按 orderNo 模糊匹配
        try:
            orders = await fetch_my_orders(user_id)
            print(f"[LookupOrder] fetched {len(orders)} orders")
            matched_order = None
            for order in orders:
                order_no = order.get("orderNo", "")
                match = order_number in order_no
                print(f"[LookupOrder]  compare: '{order_number}' in '{order_no}' -> {match}")
                if match:
                    matched_order = order
                    break

            if matched_order:
                order_id = matched_order.get("orderId")
                print(f"[LookupOrder] matched orderId={order_id}")
                if order_id:
                    detail = await fetch_order_detail(order_id, user_id)
                    if detail:
                        return self._build_response(detail)

                # 兜底：直接用列表数据
                return self._build_response_from_list(matched_order)
        except Exception as e:
            print(f"[LookupOrder] error: {e}")
            pass

        return ActionResult(
            messages=[BotMessage(text=f"未找到订单 {order_number} 的信息。请确认订单号是否正确。")]
        )

    def _build_response(self, detail: dict[str, Any]) -> ActionResult:
        """从订单详情构建回复。"""
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

    def _build_response_from_list(self, order: dict[str, Any]) -> ActionResult:
        """从订单列表数据直接构建回复（兜底）。"""
        status = STATUS_MAP.get(order.get("orderStatusCode", ""), order.get("orderStatusCode", ""))
        items = order.get("orderItems", [])
        item_info = ""
        if items:
            item = items[0]
            item_info = f"报名课程：{item.get('seriesName', '')} - {item.get('cohortName', '')}"

        msg = (
            f"订单号：{order.get('orderNo', '')}\n"
            f"订单状态：{status}\n"
            f"{item_info}\n"
            f"应付金额：{order.get('payableAmount', 0)}元\n"
            f"实付金额：{order.get('paidAmount', 0)}元\n"
        )
        return ActionResult(
            messages=[BotMessage(text=msg)],
            slot_updates={"order_status": order.get("orderStatusCode", "")},
        )

    def _extract_user_id(self, sender_id: str) -> int:
        """从 sender_id 提取用户 ID。"""
        parts = sender_id.split("_")
        if len(parts) > 1 and parts[-1].isdigit():
            return int(parts[-1])
        if sender_id.isdigit():
            return int(sender_id)
        return 1
