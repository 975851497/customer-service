"""数据库基础设施。"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from edu_assist.conf.config import settings

engine = create_async_engine(settings.database_url, echo=False)
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """获取数据库会话。"""
    async with session_factory() as session:
        yield session


async def init_db() -> None:
    """初始化数据库表。"""
    from edu_assist.models.dialogue_state import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
