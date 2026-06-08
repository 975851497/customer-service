"""YAML 流程配置加载器。"""

from __future__ import annotations

from pathlib import Path

import yaml

from edu_assist.task.flow.models import Flow, FlowSlot, FlowsList


def load_flows(yaml_path: str | Path) -> FlowsList:
    """从 YAML 文件加载流程定义。"""
    path = Path(yaml_path)
    if not path.exists():
        return FlowsList()

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data:
        return FlowsList()

    slots_data = data.get("slots", {})
    slots: dict[str, Any] = {}
    for name, slot_def in slots_data.items():
        slots[name] = {
            "name": name,
            "type": slot_def.get("type", "text"),
            "label": slot_def.get("label", ""),
            "description": slot_def.get("description", ""),
        }

    flows = {}
    for flow_id, flow_def in data.get("flows", {}).items():
        flow_slots = []
        flow_slot_names = set()
        for step in flow_def.get("steps", []):
            if step.get("type") == "collect" and step.get("slot_name"):
                slot_name = step["slot_name"]
                if slot_name not in flow_slot_names and slot_name in slots:
                    flow_slot_names.add(slot_name)
                    flow_slots.append(FlowSlot(name=slot_name, **slots[slot_name]))

        flows[flow_id] = Flow(
            id=flow_id,
            name=flow_def.get("name", ""),
            description=flow_def.get("description", ""),
            steps=flow_def.get("steps", []),
            slots=flow_slots,
        )

    return FlowsList(flows=flows)
