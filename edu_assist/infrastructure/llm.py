"""LLM 基础设施。"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage

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


async def llm_ainvoke_with_messages(messages: list[BaseMessage]) -> str:
    """使用消息列表调用 LLM。"""
    llm = get_llm()
    result = await llm.ainvoke(messages)
    return result.content
