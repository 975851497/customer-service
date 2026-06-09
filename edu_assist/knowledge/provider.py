"""知识提供者注册表与内置提供者。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from edu_assist.infrastructure.http_client import get_http_client


@dataclass
class KnowledgeChunk:
    """知识块。"""
    content: str
    source: str | None = None


class KnowledgeProvider(ABC):
    """知识检索提供者。"""
    provider_id: str = ""

    @abstractmethod
    async def retrieve(self, state: Any) -> list[str]:
        """检索知识块，返回文本列表。"""
        ...


class CourseSeriesProvider(KnowledgeProvider):
    """课程系列信息提供者。"""
    provider_id = "api.course_series"

    async def retrieve(self, state: Any) -> list[str]:
        client = get_http_client()
        chunks: list[str] = []

        # 如果有聚焦对象且类型为 series，查询该课程详情
        if state.focused_object and state.focused_object.type == "series":
            try:
                resp = await client.get(f"/api/v1/series/{state.focused_object.id}")
                data = resp.json()
                if data.get("code") == 0 and data.get("data"):
                    s = data["data"]
                    text = (
                        f"课程名称：{s.get('seriesName', '')}\n"
                        f"课程介绍：{s.get('description', '')}\n"
                        f"授课方式：{s.get('deliveryModeCode', '')}\n"
                        f"评分：{s.get('avgScore', 0)}分（共{s.get('reviewCount', 0)}条评价）"
                    )
                    chunks.append(text)

                    # 查询在售班次
                    cohorts_resp = await client.get(f"/api/v1/series/{state.focused_object.id}/cohorts")
                    cohorts_data = cohorts_resp.json()
                    if cohorts_data.get("code") == 0 and cohorts_data.get("data"):
                        cohort_lines = ["在售班次："]
                        for c in cohorts_data["data"][:5]:
                            price = c.get("salePrice", "待定")
                            start = c.get("startDate", "")
                            teacher = c.get("headTeacherName", "")
                            cohort_lines.append(
                                f"  - {c['cohortName']}（开课：{start}，价格：{price}元，班主任：{teacher}）"
                            )
                        chunks.append("\n".join(cohort_lines))
            except Exception:
                pass

        # 通用搜索：如果 active_task 有 series_name，尝试查询
        if not chunks and state.active_task:
            series_name = state.active_task.slots.get("series_name", "")
            if series_name:
                try:
                    resp = await client.get("/api/v1/series", params={"keyword": series_name})
                    data = resp.json()
                    if data.get("code") == 0:
                        series_list = data.get("data", {}).get("list", [])
                        if series_list:
                            items = []
                            for s in series_list[:5]:
                                items.append(
                                    f"  - {s.get('seriesName', '')}（评分：{s.get('avgScore', 0)}，"
                                    f"授课方式：{s.get('deliveryModeCode', '')}）"
                                )
                            chunks.append("相关课程：\n" + "\n".join(items))
                except Exception:
                    pass

        # 兜底：拿用户当前输入做关键字搜索
        if not chunks and state.pending_turn and state.pending_turn.user_message.text:
            keyword = state.pending_turn.user_message.text.strip()
            if keyword:
                try:
                    resp = await client.get("/api/v1/series", params={"keyword": keyword})
                    data = resp.json()
                    if data.get("code") == 0:
                        series_list = data.get("data", {}).get("list", [])
                        if series_list:
                            items = []
                            for s in series_list[:5]:
                                cohorts_resp = await client.get(f"/api/v1/series/{s['seriesId']}/cohorts")
                                cohorts_data = cohorts_resp.json()
                                cohort_info = ""
                                if cohorts_data.get("code") == 0 and cohorts_data.get("data"):
                                    cohort = cohorts_data["data"][0] if cohorts_data["data"] else {}
                                    price = cohort.get("salePrice", "待定")
                                    start = cohort.get("startDate", "")
                                    teacher = cohort.get("headTeacherName", "")
                                    cohort_info = f"（价格：{price}元，开课：{start}，班主任：{teacher}）"

                                items.append(
                                    f"  - {s.get('seriesName', '')}：{s.get('description', '')} "
                                    f"评分：{s.get('avgScore', 0)}分{cohort_info}"
                                )
                            chunks.append("为您找到以下课程：\n" + "\n".join(items))
                except Exception:
                    pass

        return chunks


class CohortProvider(KnowledgeProvider):
    """班次信息提供者。"""
    provider_id = "api.cohort"

    async def retrieve(self, state: Any) -> list[str]:
        client = get_http_client()
        chunks: list[str] = []

        if state.focused_object and state.focused_object.type == "cohort":
            try:
                resp = await client.get(f"/api/v1/cohorts/{state.focused_object.id}")
                data = resp.json()
                if data.get("code") == 0 and data.get("data"):
                    c = data["data"]
                    text = (
                        f"班次名称：{c.get('cohortName', '')}\n"
                        f"所属课程：{c.get('seriesName', '')}\n"
                        f"授课方式：{c.get('deliveryModeCode', '')}\n"
                        f"价格：{c.get('salePrice', '待定')}元\n"
                        f"开课日期：{c.get('startDate', '')}\n"
                        f"结课日期：{c.get('endDate', '待定')}\n"
                        f"班主任：{c.get('headTeacherName', '待定')}\n"
                        f"已报名：{c.get('currentStudentCount', 0)}人"
                    )
                    chunks.append(text)
            except Exception:
                pass

        return chunks


class OrderProvider(KnowledgeProvider):
    """订单信息提供者。"""
    provider_id = "api.order"

    async def retrieve(self, state: Any) -> list[str]:
        client = get_http_client()
        chunks: list[str] = []

        # 从 sender_id 提取 user_id
        user_id = self._extract_user_id(state.sender_id)

        try:
            resp = await client.get(
                "/api/v1/orders",
                headers={"X-User-Id": str(user_id)},
            )
            data = resp.json()
            if data.get("code") == 0:
                orders = data.get("data", {}).get("list", [])
                if orders:
                    lines = ["你的订单："]
                    for o in orders[:5]:
                        status_map = {
                            "pending": "待支付", "paid": "已支付", "completed": "已完成",
                            "cancelled": "已取消", "partial_refunded": "部分退款", "refunded": "已退款",
                        }
                        status = status_map.get(o.get("orderStatusCode", ""), o.get("orderStatusCode", ""))
                        items = o.get("orderItems", [])
                        course = items[0].get("cohortName", "") if items else ""
                        lines.append(f"  - {o['orderNo']}（{course}，{status}，{o.get('payableAmount', 0)}元）")
                    chunks.append("\n".join(lines))
        except Exception:
            pass

        return chunks

    def _extract_user_id(self, sender_id: str) -> int:
        parts = sender_id.split("_")
        if len(parts) > 1 and parts[-1].isdigit():
            return int(parts[-1])
        return 1


class ProgressProvider(KnowledgeProvider):
    """学习进度信息提供者。"""
    provider_id = "api.progress"

    async def retrieve(self, state: Any) -> list[str]:
        client = get_http_client()
        chunks: list[str] = []

        user_id = self._extract_user_id(state.sender_id)

        try:
            # 获取用户的班次列表
            cohorts_resp = await client.get(
                "/api/v1/me/cohorts",
                headers={"X-User-Id": str(user_id)},
            )
            cohorts_data = cohorts_resp.json()
            if cohorts_data.get("code") != 0:
                return chunks

            cohorts = cohorts_data.get("data", {}).get("list", [])
            if not cohorts:
                return chunks

            # 取第一个活跃班次查询进度
            for cohort in cohorts[:3]:
                cohort_id = cohort.get("cohortId")
                if not cohort_id:
                    continue

                progress_resp = await client.get(
                    f"/api/v1/me/cohorts/{cohort_id}/progress",
                    headers={"X-User-Id": str(user_id)},
                )
                progress_data = progress_resp.json()
                if progress_data.get("code") == 0 and progress_data.get("data"):
                    p = progress_data["data"]
                    att = p.get("attendance", {})
                    vid = p.get("video", {})
                    hw = p.get("homework", {})
                    ex = p.get("exam", {})

                    text = (
                        f"【{cohort.get('cohortName', '')}】\n"
                        f"考勤：出勤{att.get('presentCount', 0)}次/缺勤{att.get('absentCount', 0)}次（共{att.get('totalSessions', 0)}次）\n"
                        f"视频：完成{vid.get('completedVideos', 0)}个/共{vid.get('totalVideos', 0)}个\n"
                        f"作业：提交{hw.get('submittedCount', 0)}个/共{hw.get('totalHomeworks', 0)}个"
                    )
                    if hw.get("correctedCount", 0) > 0:
                        text += f"（已批改{hw.get('correctedCount', 0)}个）"
                    text += f"\n考试：参加{ex.get('submittedCount', 0)}场/共{ex.get('totalExams', 0)}场"
                    chunks.append(text)
        except Exception:
            pass

        return chunks

    def _extract_user_id(self, sender_id: str) -> int:
        parts = sender_id.split("_")
        if len(parts) > 1 and parts[-1].isdigit():
            return int(parts[-1])
        return 1


class FAQProvider(KnowledgeProvider):
    """FAQ 知识库提供者（占位，可扩展接入向量检索）。"""
    provider_id = "faq.default"

    async def retrieve(self, state: Any) -> list[str]:
        # 当前为占位，返回基本的退款政策说明
        # 后续可接入向量知识库或 FAQ 匹配
        return [
            "退款政策：学员在开课前申请退款可全额退款；开课后按已完成课时比例扣除费用。"
            "具体退款金额以订单实际支付金额为准，优惠券抵扣部分不退还。"
        ]


class KnowledgeProviderRegistry:
    """知识提供者注册表。"""

    def __init__(self) -> None:
        self._providers: dict[str, KnowledgeProvider] = {}
        self._intents: dict[str, dict[str, Any]] = {}

    def register_provider(self, provider: KnowledgeProvider) -> None:
        """注册提供者。"""
        self._providers[provider.provider_id] = provider

    def register_intent(self, intent_id: str, description: str, provider_ids: list[str], requires_object: bool = False) -> None:
        """注册知识意图。"""
        self._intents[intent_id] = {
            "id": intent_id,
            "description": description,
            "provider_ids": provider_ids,
            "requires_object": requires_object,
        }

    def get_provider(self, provider_id: str) -> KnowledgeProvider | None:
        return self._providers.get(provider_id)

    def get_intent(self, intent_id: str) -> dict[str, Any] | None:
        return self._intents.get(intent_id)

    def get_intents_json(self) -> str:
        """获取所有意图的 JSON。"""
        import json
        return json.dumps(
            [{"id": k, "description": v["description"]} for k, v in self._intents.items()],
            ensure_ascii=False,
        )
