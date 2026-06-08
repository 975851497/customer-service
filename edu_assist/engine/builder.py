"""引擎构建器（组合根）。"""

from __future__ import annotations

import json
from pathlib import Path

from edu_assist.clarify.handler import ClarifyResponder
from edu_assist.chitchat.handler import ChitchatHandler
from edu_assist.engine.engine import DialogueEngine
from edu_assist.knowledge.handler import KnowledgeHandler
from edu_assist.knowledge.provider import KnowledgeProvider, KnowledgeProviderRegistry
from edu_assist.plan.planner import TurnPlanner
from edu_assist.plan.validator import TurnPlanValidator
from edu_assist.task.action.builder import register_builtin_actions, register_custom_actions
from edu_assist.task.action.registry import ActionRegistry
from edu_assist.task.action.runner import ActionRunner
from edu_assist.task.command import CommandProcessor
from edu_assist.task.flow.executor import FlowExecutor
from edu_assist.task.flow.loader import load_flows
from edu_assist.task.handler import TaskHandler

_engine: DialogueEngine | None = None


def build_dialogue_engine() -> DialogueEngine:
    """构建对话引擎（组合根）。"""
    global _engine
    if _engine is not None:
        return _engine

    # 加载流程定义
    base_dir = Path(__file__).resolve().parent.parent.parent
    user_flows_path = base_dir / "flow_config" / "user_flows.yml"
    system_flows_path = base_dir / "flow_config" / "system_flows.yml"

    user_flows = load_flows(user_flows_path)
    system_flows = load_flows(system_flows_path)

    # 注册动作
    registry = ActionRegistry()
    register_builtin_actions(registry)
    register_custom_actions(registry)

    action_runner = ActionRunner(registry)
    flow_executor = FlowExecutor(user_flows, system_flows, action_runner)
    command_processor = CommandProcessor()
    task_handler = TaskHandler(command_processor, flow_executor)

    # 知识模块
    provider_registry = KnowledgeProviderRegistry()

    # 注册教育知识意图
    provider_registry.register_intent("course_info", "用户想了解课程系列的信息，如课程内容、适用人群、价格等", ["api.course_series", "api.cohort"])
    provider_registry.register_intent("cohort_info", "用户想了解具体班次的信息，如开课时间、授课老师、价格等", ["api.cohort"])
    provider_registry.register_intent("order_info", "用户想了解订单信息，如订单状态、支付情况等", ["api.order"])
    provider_registry.register_intent("learning_progress", "用户想了解学习进度，如考勤、视频完成情况、作业、考试成绩等", ["api.progress"])
    provider_registry.register_intent("refund_policy", "用户想了解退款政策", ["faq.default"])
    provider_registry.register_intent("platform_rule", "用户想了解平台规则", ["faq.default"])

    knowledge_handler = KnowledgeHandler(provider_registry)

    # 闲聊
    chitchat_handler = ChitchatHandler()

    # 澄清
    clarify_responder = ClarifyResponder()

    # 构建可用流程列表 JSON
    available_flows = json.dumps(
        [
            {"id": fid, "name": f.name, "description": f.description}
            for fid, f in user_flows.flows.items()
        ],
        ensure_ascii=False,
    )

    # 回合规划器
    turn_planner = TurnPlanner(
        available_flows=available_flows,
        knowledge_intents=provider_registry.get_intents_json(),
    )
    turn_validator = TurnPlanValidator()

    # 引擎
    _engine = DialogueEngine(
        turn_planner=turn_planner,
        turn_validator=turn_validator,
        task_handler=task_handler,
        knowledge_handler=knowledge_handler,
        chitchat_handler=chitchat_handler,
        clarify_responder=clarify_responder,
    )
    return _engine


def get_engine() -> DialogueEngine:
    """获取引擎实例。"""
    return build_dialogue_engine()
