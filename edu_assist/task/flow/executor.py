"""流程执行器。"""

from __future__ import annotations

from typing import Any

from edu_assist.domain.state import (
    DialogueState,
    SYSTEM_COLLECT_INFORMATION,
    SystemContext,
    TaskContext,
)
from edu_assist.domain.messages import BotMessage
from edu_assist.task.action.base import ActionCall
from edu_assist.task.action.runner import ActionRunner
from edu_assist.task.flow.links import evaluate_links, parse_next
from edu_assist.task.flow.models import FlowsList


class ActionCallResult:
    """Action 调用结果。"""
    def __init__(self, action_name: str, args: dict[str, Any]) -> None:
        self.action_name = action_name
        self.args = args


class FlowExecutor:
    """流程执行引擎。"""

    def __init__(self, user_flows: FlowsList, system_flows: FlowsList, action_runner: ActionRunner) -> None:
        self._user_flows = user_flows
        self._system_flows = system_flows
        self._action_runner = action_runner

    def _get_flow(self, flow_id: str, is_system: bool = False) -> Any:
        flows = self._system_flows if is_system else self._user_flows
        return flows.flows.get(flow_id)

    def _get_step(self, flow: Any, step_id: str) -> dict[str, Any] | None:
        for step in flow.steps:
            if step["id"] == step_id:
                return step
        return None

    async def run_task(self, state: DialogueState, task: Any | None = None) -> list[BotMessage]:
        """执行当前任务（active_task 或 active_system_task）。"""
        if task is None:
            task = state.active_task or state.active_system_task
            if task is None:
                return []
        else:
            # 确保 state 的引用与 task 同步
            if task is state.active_system_task:
                pass
            elif task is not state.active_task:
                return []

        flow_id = task.flow_id
        is_system = isinstance(task, SystemContext)
        flow = self._get_flow(flow_id, is_system=is_system)

        if flow is None:
            state.end_system_task() if is_system else state.end_active_task()
            return [BotMessage(text=f"未找到流程: {flow_id}")]

        messages: list[BotMessage] = []
        processed_actions: set[str] = set()

        while True:
            step = self._get_step(flow, task.step_id)
            if step is None:
                break

            step_type = step["type"]
            next_links = parse_next(step.get("next", []))

            if step_type == "start":
                task_slots = getattr(task, "slots", {})
                task.step_id = evaluate_links(next_links, task_slots) or ""
                continue

            elif step_type == "end":
                if is_system:
                    state.end_system_task()
                else:
                    state.end_active_task()
                break

            elif step_type == "collect":
                slot_name = step.get("slot_name", "")
                response_cfg = step.get("response", {})
                validation = step.get("validation")
                fail_resp = step.get("failure_response", {})

                # 自动填充聚焦对象
                if state.focused_object:
                    obj = state.focused_object
                    if obj.type == "order" and slot_name == "order_number":
                        state.set_slots({"order_number": obj.id})
                    elif obj.type == "cohort" and slot_name in ("cohort_id", "cohort_name"):
                        state.set_slots({slot_name: obj.id})
                    elif obj.type == "series" and slot_name == "series_name":
                        state.set_slots({"series_name": obj.id})

                # 检查 slot 是否有值
                slot_value = task.slots.get(slot_name) if isinstance(task, TaskContext) else None

                if slot_value is not None:
                    if validation:
                        try:
                            if not eval(validation, {"value": slot_value, "slots": task.slots}):
                                state.remove_slot(slot_name)
                                if fail_resp.get("text"):
                                    messages.append(BotMessage(text=fail_resp["text"]))
                                continue
                        except Exception:
                            pass
                    # slot 有值，继续
                    next_step = evaluate_links(next_links, task.slots)

                    # 检查是否有占位 action
                    action_name = step.get("action", "")
                    if action_name and action_name != "action_listen":
                        args = step.get("args", {})
                        action_call = ActionCall(action_name, args, next_step or "")
                        action_key = f"{task.step_id}_{action_name}"
                        if action_key not in processed_actions:
                            processed_actions.add(action_key)
                            result = await self._action_runner.run(action_call, state, task.slots)
                            if result.messages:
                                messages.extend(result.messages)
                            if result.slot_updates:
                                state.set_slots(result.slot_updates)
                    task.step_id = next_step or ""
                    continue

                # slot 没有值，启动收集流程
                state.start_system_task(SYSTEM_COLLECT_INFORMATION, {
                    "slot_name": slot_name,
                    "response_text": response_cfg.get("text", f"请提供{slot_name}。"),
                    "validation": validation,
                    "failure_response": fail_resp.get("text", ""),
                    "target_step_id": task.step_id,
                    "target_flow_id": flow_id,
                })
                # 添加提示消息
                msg_text = response_cfg.get("text", f"请提供{slot_name}。")
                messages.append(BotMessage(text=msg_text))
                break  # 等待用户输入

            elif step_type == "action":
                action_name = step.get("action", "")
                args = step.get("args", {})

                # 渲染 args 中的 Jinja2 模板
                rendered_args: dict[str, Any] = {}
                template_vars = {"slots": getattr(task, "slots", {})}
                if hasattr(task, "context"):
                    template_vars["context"] = task.context
                for key, value in args.items():
                    if isinstance(value, str) and "{{" in value:
                        from jinja2 import Template
                        try:
                            rendered_args[key] = Template(value).render(**template_vars)
                        except Exception:
                            rendered_args[key] = value
                    else:
                        rendered_args[key] = value

                if action_name == "action_listen":
                    break

                task_slots = getattr(task, "slots", {})
                next_step = evaluate_links(next_links, task_slots)
                action_call = ActionCall(action_name, rendered_args, next_step or "")
                result = await self._action_runner.run(action_call, state, task_slots)

                if result.messages:
                    messages.extend(result.messages)
                if result.slot_updates:
                    state.set_slots(result.slot_updates)

                task.step_id = next_step or ""
                continue

            else:
                break

        return messages
