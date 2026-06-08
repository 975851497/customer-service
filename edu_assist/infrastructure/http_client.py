"""HTTP 客户端基础设施。"""

from __future__ import annotations

import httpx

from edu_assist.conf.config import settings

_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """获取 HTTP 客户端实例（单例）。"""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(base_url=settings.edu_api_base_url, timeout=30.0)
    return _client


async def close_http_client() -> None:
    """关闭 HTTP 客户端。"""
    global _client
    if _client:
        await _client.aclose()
        _client = None
