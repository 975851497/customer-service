"""对话状态 ORM 模型。"""

from __future__ import annotations

from sqlalchemy import Column, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class DialogueStateRecord(Base):
    __tablename__ = "dialogue_states"

    sender_id = Column(String(255), primary_key=True)
    state_json = Column(Text, nullable=False)
