"""FastAPI 路由定义。"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from edu_assist.api.schemas import (
    ChatBotMessage,
    ChatObject,
    ChatRequest,
    ChatResponse,
    HistoryMessage,
    HistoryResponse,
    SessionStateResponse,
)
from edu_assist.domain.messages import MessageObject, MessageType, UserMessage
from edu_assist.engine.builder import get_engine
from edu_assist.infrastructure.database import get_db
from edu_assist.repository.state_repository import DialogueStateRepository
from edu_assist.service.dialogue_service import DialogueService

router = APIRouter(prefix="/api/chat", tags=["chat"])


async def _get_dialogue_service(db: AsyncSession = Depends(get_db)) -> DialogueService:
    engine = get_engine()
    repository = DialogueStateRepository(db)
    return DialogueService(engine, repository)


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: DialogueService = Depends(_get_dialogue_service),
) -> ChatResponse:
    """发送对话消息。"""
    message_object = None
    if request.object:
        message_object = MessageObject(
            type=request.object.type,
            id=request.object.id,
            title=request.object.title,
            attributes=request.object.attributes,
        )

    user_message = UserMessage(
        sender_id=request.sender_id,
        message_id=request.message_id or "",
        type=MessageType.OBJECT if request.object else MessageType.TEXT,
        text=request.text,
        object=message_object,
    )

    result = await service.process_message(request.sender_id, user_message)

    return ChatResponse(
        sender_id=result["sender_id"],
        message_id=result["message_id"],
        messages=[
            ChatBotMessage(
                text=msg.get("text"),
                object=ChatObject(**msg["object"]) if msg.get("object") else None,
            )
            for msg in result.get("messages", [])
        ],
    )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    service: DialogueService = Depends(_get_dialogue_service),
):
    """发送对话消息（SSE 流式响应）- 真实流式输出。"""
    message_object = None
    if request.object:
        message_object = MessageObject(
            type=request.object.type,
            id=request.object.id,
            title=request.object.title,
            attributes=request.object.attributes,
        )

    user_message = UserMessage(
        sender_id=request.sender_id,
        message_id=request.message_id or "",
        type=MessageType.OBJECT if request.object else MessageType.TEXT,
        text=request.text,
        object=message_object,
    )

    async def event_stream():
        try:
            async for event in service.process_message_stream(request.sender_id, user_message):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            error = json.dumps({"type": "error", "text": f"处理失败: {str(e)}"}, ensure_ascii=False)
            yield f"data: {error}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history", response_model=HistoryResponse)
async def chat_history(
    sender_id: str = Query(..., description="用户标识"),
    service: DialogueService = Depends(_get_dialogue_service),
) -> HistoryResponse:
    """获取聊天历史。"""
    result = await service.get_history(sender_id)
    return HistoryResponse(
        sender_id=result["sender_id"],
        messages=[
            HistoryMessage(
                role=msg["role"],
                text=msg.get("text"),
                object=ChatObject(**msg["object"]) if msg.get("object") else None,
            )
            for msg in result.get("messages", [])
        ],
    )


@router.get("/session", response_model=SessionStateResponse)
async def session_state(
    sender_id: str = Query(..., description="用户标识"),
    service: DialogueService = Depends(_get_dialogue_service),
) -> SessionStateResponse:
    """获取当前会话状态。"""
    result = await service.get_session_state(sender_id)
    return SessionStateResponse(
        sender_id=result["sender_id"],
        session_id=result.get("session_id"),
        has_active_task=result.get("has_active_task", False),
        active_task_flow_id=result.get("active_task_flow_id"),
        active_task_name=result.get("active_task_name"),
        slots=result.get("active_task_slots", {}),
        paused_task_count=result.get("paused_task_count", 0),
    )
