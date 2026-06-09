"""查询课程系列信息动作。"""

from __future__ import annotations

from typing import Any

from edu_assist.task.action.base import Action, ActionResult
from edu_assist.domain.messages import BotMessage
from edu_assist.task.action.custom.shared import fetch_series_detail, fetch_series_list, fetch_series_cohorts


class LookupCourseSeriesAction(Action):
    """查询课程系列信息。"""
    name = "action_lookup_course_series"

    async def run(self, state: Any, action_kwargs: dict[str, Any]) -> ActionResult:
        series_name = action_kwargs.get("series_name", "")
        series_id = action_kwargs.get("series_id", "")

        if series_id:
            try:
                detail = await fetch_series_detail(int(series_id))
                if detail:
                    cohorts = await fetch_series_cohorts(int(series_id))
                    cohort_info = ""
                    if cohorts:
                        cohort_list = []
                        for c in cohorts[:3]:
                            price = c.get("salePrice", "待定")
                            start = c.get("startDate", "")
                            cohort_list.append(f"  - {c['cohortName']}（开课：{start}，价格：{price}元）")
                        cohort_info = "\n在售班次：\n" + "\n".join(cohort_list)

                    msg = (
                        f"【{detail.get('seriesName', '')}】\n"
                        f"{detail.get('description', '暂无介绍')}\n"
                        f"授课方式：{detail.get('deliveryModeCode', '')}\n"
                        f"平均评分：{detail.get('avgScore', 0)}分\n"
                        f"{cohort_info}"
                    )
                    return ActionResult(
                        messages=[BotMessage(text=msg)],
                        slot_updates={"series_name": detail.get("seriesName", "")},
                    )
            except (ValueError, TypeError):
                pass

        if series_name:
            series_list = await fetch_series_list(keyword=series_name)
            if series_list:
                items = []
                for s in series_list[:5]:
                    items.append(f"  - {s.get('seriesName', '')}（评分：{s.get('avgScore', 0)}）")
                msg = f"为您找到以下课程：\n" + "\n".join(items) + "\n\n请输入课程编号或名称查看详细信息。"
                return ActionResult(messages=[BotMessage(text=msg)])
            # 尝试拆解关键词再搜索
            for part in series_name.split():
                part_list = await fetch_series_list(keyword=part)
                if part_list:
                    items = []
                    for s in part_list[:5]:
                        items.append(f"  - {s.get('seriesName', '')}（评分：{s.get('avgScore', 0)}）")
                    msg = f"未找到「{series_name}」，但为您找到以下相关课程：\n" + "\n".join(items)
                    return ActionResult(messages=[BotMessage(text=msg)])

        # 未找到时清除 slot，让流程正常结束
        return ActionResult(
            messages=[BotMessage(text="暂未找到相关课程信息，请尝试其他关键词。")],
            slot_updates={"series_name": None},
        )
