"""共享 API 工具 - 调用教育系统 API。"""

from __future__ import annotations

from typing import Any

from edu_assist.infrastructure.http_client import get_http_client


async def fetch_series_detail(series_id: int) -> dict[str, Any] | None:
    """查询课程系列详情。"""
    client = get_http_client()
    try:
        resp = await client.get(f"/api/v1/series/{series_id}")
        data = resp.json()
        return data.get("data") if data.get("code") == 0 else None
    except Exception:
        return None


async def fetch_series_list(keyword: str | None = None) -> list[dict[str, Any]]:
    """查询课程系列列表。"""
    client = get_http_client()
    params = {}
    if keyword:
        params["keyword"] = keyword
    try:
        resp = await client.get("/api/v1/series", params=params)
        data = resp.json()
        if data.get("code") == 0:
            return data.get("data", {}).get("list", [])
        return []
    except Exception:
        return []


async def fetch_cohort_detail(cohort_id: int) -> dict[str, Any] | None:
    """查询班次详情。"""
    client = get_http_client()
    try:
        resp = await client.get(f"/api/v1/cohorts/{cohort_id}")
        data = resp.json()
        return data.get("data") if data.get("code") == 0 else None
    except Exception:
        return None


async def fetch_series_cohorts(series_id: int) -> list[dict[str, Any]]:
    """查询课程系列的班次列表。"""
    client = get_http_client()
    try:
        resp = await client.get(f"/api/v1/series/{series_id}/cohorts")
        data = resp.json()
        if data.get("code") == 0:
            return data.get("data", [])
        return []
    except Exception:
        return []


async def fetch_order_detail(order_id: int, user_id: int) -> dict[str, Any] | None:
    """查询订单详情。"""
    client = get_http_client()
    try:
        resp = await client.get(
            f"/api/v1/orders/{order_id}",
            headers={"X-User-Id": str(user_id)},
        )
        data = resp.json()
        return data.get("data") if data.get("code") == 0 else None
    except Exception:
        return None


async def fetch_my_cohort_progress(cohort_id: int, user_id: int) -> dict[str, Any] | None:
    """查询学习进度。"""
    client = get_http_client()
    try:
        resp = await client.get(
            f"/api/v1/me/cohorts/{cohort_id}/progress",
            headers={"X-User-Id": str(user_id)},
        )
        data = resp.json()
        return data.get("data") if data.get("code") == 0 else None
    except Exception:
        return None


async def fetch_my_cohorts(user_id: int) -> list[dict[str, Any]]:
    """查询我的班次列表。"""
    client = get_http_client()
    try:
        resp = await client.get(
            "/api/v1/me/cohorts",
            headers={"X-User-Id": str(user_id)},
        )
        data = resp.json()
        if data.get("code") == 0:
            return data.get("data", {}).get("list", [])
        return []
    except Exception:
        return []


async def create_refund_request(
    order_item_id: int,
    refund_type: str,
    refund_reason: str,
    apply_amount: float,
    user_id: int,
) -> dict[str, Any] | None:
    """创建退款申请。"""
    client = get_http_client()
    try:
        resp = await client.post(
            f"/api/v1/order-items/{order_item_id}/refund-requests",
            json={
                "refundType": refund_type,
                "refundReason": refund_reason,
                "applyAmount": apply_amount,
            },
            headers={"X-User-Id": str(user_id)},
        )
        data = resp.json()
        return data.get("data") if data.get("code") == 0 else None
    except Exception:
        return None


async def create_service_ticket(
    ticket_type: str,
    title: str,
    content: str,
    student_id: int,
    order_item_id: int,
    user_id: int,
    priority: str = "medium",
) -> dict[str, Any] | None:
    """创建工单。"""
    client = get_http_client()
    try:
        resp = await client.post(
            "/api/v1/service-tickets",
            json={
                "ticketType": ticket_type,
                "priorityLevel": priority,
                "ticketSource": "customer_service",
                "title": title,
                "ticketContent": content,
                "studentId": student_id,
                "orderItemId": order_item_id,
            },
            headers={"X-User-Id": str(user_id)},
        )
        data = resp.json()
        return data.get("data") if data.get("code") == 0 else None
    except Exception:
        return None


async def fetch_my_orders(user_id: int, status: str | None = None) -> list[dict[str, Any]]:
    """查询我的订单列表。"""
    client = get_http_client()
    params = {}
    if status:
        params["status"] = status
    try:
        resp = await client.get(
            "/api/v1/orders",
            params=params,
            headers={"X-User-Id": str(user_id)},
        )
        data = resp.json()
        print(f"\n[fetch_my_orders] user_id={user_id}, status={resp.status_code}, code={data.get('code')}, total={data.get('data',{}).get('total', 'N/A')}")
        if data.get("code") == 0:
            return data.get("data", {}).get("list", [])
        return []
    except Exception as e:
        print(f"[fetch_my_orders] error: {e}")
        return []


async def fetch_student_profile(user_id: int) -> dict[str, Any] | None:
    """获取当前用户的学员档案信息。"""
    client = get_http_client()
    try:
        resp = await client.get(
            "/api/v1/me/student-profile",
            headers={"X-User-Id": str(user_id)},
        )
        data = resp.json()
        return data.get("data") if data.get("code") == 0 else None
    except Exception:
        return None
