"""对话历史格式化工具。"""

from __future__ import annotations


class HistoryBuilder:
    """对话历史构建器。"""

    @staticmethod
    def build(state: object) -> str:
        """将回合列表格式化为 USER:/BOT: 文本。"""
        lines = []
        try:
            session = getattr(state, "current_session", None)
            if session is None:
                return ""
            for turn in getattr(session, "turns", [])[-10:]:
                user_msg = turn.user_message
                if user_msg.text:
                    lines.append(f"USER: {user_msg.text}")
                elif user_msg.object:
                    obj = user_msg.object
                    attrs = ", ".join(f"{k}={v}" for k, v in obj.attributes.items())
                    lines.append(f"USER: [{obj.type} id={obj.id}, title={obj.title}, {attrs}]")
                for bot_msg in turn.bot_messages:
                    if bot_msg.text:
                        lines.append(f"BOT: {bot_msg.text}")
        except Exception:
            return ""
        return "\n".join(lines)
