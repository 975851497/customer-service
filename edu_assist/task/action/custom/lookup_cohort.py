"""查询班次信息动作。"""

from __future__ import annotations

from typing import Any

from edu_assist.task.action.base import Action, ActionResult
from edu_assist.domain.messages import BotMessage
from edu_assist.task.action.custom.shared import fetch_cohort_detail


class LookupCohortAction(Action):
    """查询班次信息。"""
    name = "action_lookup_cohort"

    async def run(self, state: Any, action_kwargs: dict[str, Any]) -> ActionResult:
        cohort_id = action_kwargs.get("cohort_id", "")
        cohort_name = action_kwargs.get("cohort_name", "")

        if cohort_id:
            try:
                detail = await fetch_cohort_detail(int(cohort_id))
                if detail:
                    msg = (
                        f"【{detail.get('cohortName', '')}】\n"
                        f"所属课程：{detail.get('seriesName', '')}\n"
                        f"授课方式：{detail.get('deliveryModeCode', '')}\n"
                        f"价格：{detail.get('salePrice', '待定')}元\n"
                        f"开课日期：{detail.get('startDate', '')}\n"
                        f"结课日期：{detail.get('endDate', '')}\n"
                        f"班主任：{detail.get('headTeacherName', '待定')}\n"
                        f"当前报名：{detail.get('currentStudentCount', 0)}人"
                    )
                    return ActionResult(
                        messages=[BotMessage(text=msg)],
                        slot_updates={"cohort_name": detail.get("cohortName", "")},
                    )
            except (ValueError, TypeError):
                pass

        return ActionResult(
            messages=[BotMessage(text=f"暂未找到班次信息（班次：{cohort_name or cohort_id}）。")]
        )
