"""对话状态持久化仓库。"""

from __future__ import annotations

import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from edu_assist.domain.state import DialogueState
from edu_assist.models.dialogue_state import DialogueStateRecord


class DialogueStateRepository:
    """对话状态数据仓库。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def load_state(self, sender_id: str) -> DialogueState:
        """从数据库加载对话状态。"""
        record = await self._session.get(DialogueStateRecord, sender_id)
        if record is None:
            return DialogueState(sender_id=sender_id)
        data = json.loads(record.state_json)
        return DialogueState.model_validate(data)

    async def save_state(self, state: DialogueState) -> None:
        """保存对话状态到数据库。"""
        state_json = state.model_dump_json()
        await self._session.execute(
            text("""
                INSERT INTO dialogue_states (sender_id, state_json)
                VALUES (:sender_id, :state_json)
                ON DUPLICATE KEY UPDATE state_json = :state_json2
            """),
            {
                "sender_id": state.sender_id,
                "state_json": state_json,
                "state_json2": state_json,
            },
        )
        await self._session.commit()
