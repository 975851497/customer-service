"""知识提供者注册表与内置提供者。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


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
