"""LLM 基础设施。"""

from __future__ import annotations

from collections.abc import AsyncIterator

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from edu_assist.conf.config import settings


_llm: ChatOpenAI | None = None


def get_llm() -> ChatOpenAI:
    """获取 LLM 实例（单例）。"""
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            temperature=0.1,
        )
    return _llm


async def llm_ainvoke(prompt: str) -> str:
    """调用 LLM 并返回文本结果。"""
    llm = get_llm()
    result = await llm.ainvoke(prompt)
    return result.content


async def llm_astream(prompt: str) -> AsyncIterator[str]:
    """流式调用 LLM，逐块产出 token。"""
    llm = get_llm()
    async for chunk in llm.astream(prompt):
        if chunk.content:
            yield chunk.content


async def llm_astream_messages(messages: list[BaseMessage]) -> AsyncIterator[str]:
    """流式调用 LLM（messages 格式），逐块产出 token。"""
    llm = get_llm()
    async for chunk in llm.astream(messages):
        if chunk.content:
            yield chunk.content
