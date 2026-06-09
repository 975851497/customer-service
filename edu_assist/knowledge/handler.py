"""知识问答模块。"""

from __future__ import annotations

from typing import Any

from edu_assist.domain.messages import BotMessage
from edu_assist.infrastructure.llm import llm_ainvoke
from edu_assist.prompts.prompt_loader import load_prompt
from edu_assist.prompts.history_builder import HistoryBuilder
from edu_assist.knowledge.provider import KnowledgeProviderRegistry


class KnowledgeHandler:
    """知识查询处理器。"""

    def __init__(self, provider_registry: KnowledgeProviderRegistry) -> None:
        self._provider_registry = provider_registry

    async def handle(self, intents: list[str], state: Any, user_message_text: str) -> list[BotMessage]:
        """处理知识查询。"""
        # 去重并收集 provider_ids
        provider_ids = set()
        for intent_id in intents:
            intent = self._provider_registry.get_intent(intent_id)
            if intent:
                provider_ids.update(intent.get("provider_ids", []))

        # 并行检索
        chunks: list[str] = []
        for pid in provider_ids:
            provider = self._provider_registry.get_provider(pid)
            if provider:
                results = await provider.retrieve(state)
                chunks.extend(results)

        knowledge_content = "\n".join(chunks) if chunks else "暂无相关信息。"

        # 调试日志
        print(f"\n=== KNOWLEDGE ===")
        print(f"Intents: {intents}")
        print(f"Provider IDs: {provider_ids}")
        print(f"Chunks count: {len(chunks)}")
        if chunks:
            print(f"First chunk: {chunks[0][:200]}")
        print(f"=================\n")

        # 生成回复
        try:
            history = HistoryBuilder.build(state)
            template = load_prompt("knowledge_respond.jinja2")
            prompt = template.render(
                history=history,
                user_message=user_message_text,
                knowledge_content=knowledge_content,
            )
            result = await llm_ainvoke(prompt)
            return [BotMessage(text=result)]
        except Exception:
            return [BotMessage(text=knowledge_content)]
