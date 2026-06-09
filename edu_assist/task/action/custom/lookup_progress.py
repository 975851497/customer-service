"""查询学习进度动作。"""

from __future__ import annotations

from typing import Any

from edu_assist.task.action.base import Action, ActionResult
from edu_assist.domain.messages import BotMessage
from edu_assist.task.action.custom.shared import fetch_my_cohort_progress, fetch_my_cohorts


class LookupProgressAction(Action):
    """查询学习进度。"""
    name = "action_lookup_progress"

    async def run(self, state: Any, action_kwargs: dict[str, Any]) -> ActionResult:
        cohort_name = action_kwargs.get("cohort_name", "")
        cohort_id = action_kwargs.get("cohort_id", "")

        user_id = self._extract_user_id(state.sender_id)

        # 如果没有提供班次信息，列出用户的班次
        if not cohort_name and not cohort_id:
            cohorts = await fetch_my_cohorts(user_id)
            if not cohorts:
                return ActionResult(
                    messages=[BotMessage(text="你目前没有报名任何班次。")]
                )
            items = []
            for c in cohorts:
                items.append(f"  - {c.get('cohortName', '')}（状态：{c.get('enrollStatusCode', '')}）")
            msg = "你已报名的班次：\n" + "\n".join(items) + "\n\n请告诉我你想查询哪个班次的学习进度。"
            return ActionResult(messages=[BotMessage(text=msg)])

        # 尝试查找匹配的班次 ID
        if cohort_name and not cohort_id:
            cohorts = await fetch_my_cohorts(user_id)
            for c in cohorts:
                if cohort_name in c.get("cohortName", ""):
                    cohort_id = str(c.get("cohortId", ""))
                    break

        if cohort_id:
            try:
                progress = await fetch_my_cohort_progress(int(cohort_id), user_id)
                if progress:
                    att = progress.get("attendance", {})
                    vid = progress.get("video", {})
                    hw = progress.get("homework", {})
                    ex = progress.get("exam", {})

                    msg = (
                        "【学习进度报告】\n\n"
                        f"考勤情况：出勤 {att.get('presentCount', 0)} 次 / 缺勤 {att.get('absentCount', 0)} 次（共 {att.get('totalSessions', 0)} 次）\n"
                        f"视频学习：已完成 {vid.get('completedVideos', 0)} 个 / 共 {vid.get('totalVideos', 0)} 个\n"
                        f"作业情况：已提交 {hw.get('submittedCount', 0)} 个 / 共 {hw.get('totalHomeworks', 0)} 个"
                    )
                    if hw.get('correctedCount', 0) > 0:
                        msg += f"（已批改 {hw.get('correctedCount', 0)} 个）"
                    msg += (
                        f"\n考试情况：已参加 {ex.get('submittedCount', 0)} 场 / 共 {ex.get('totalExams', 0)} 场"
                    )

                    return ActionResult(
                        messages=[BotMessage(text=msg)],
                        slot_updates={"cohort_name": cohort_name},
                    )
            except (ValueError, TypeError):
                pass

        return ActionResult(
            messages=[BotMessage(text=f"暂未查询到班次的学习进度信息。")]
        )

    def _extract_user_id(self, sender_id: str) -> int:
        parts = sender_id.split("_")
        if len(parts) > 1 and parts[-1].isdigit():
            return int(parts[-1])
        if sender_id.isdigit():
            return int(sender_id)
        return 1
