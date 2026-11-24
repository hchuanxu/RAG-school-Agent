"""对话路由。

- POST /chat              非流式对话
- POST /chat/stream       SSE 流式对话
- GET  /history           会话历史列表
- GET  /history/{id}      会话消息详情
- DELETE /history/{id}    删除会话
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import AsyncSessionLocal, get_db
from app.metrics.feedback_recorder import feedback_recorder
from app.metrics.recall_metrics import recall_metrics
from app.models.user import User
from app.schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatSessionResponse,
    SessionRenameRequest,
)
from app.schemas.common import PaginatedResponse
from app.services.chat_service import chat_service

router = APIRouter(tags=["对话"])


@router.post("/chat", summary="非流式对话")
async def chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """提交问题并返回完整回答与引用溯源。"""
    return await chat_service.chat(
        db,
        user_id=current_user.id,
        question=payload.question,
        session_id=payload.session_id,
        knowledge_base_ids=payload.knowledge_base_ids,
    )


@router.post("/chat/stream", summary="流式对话")
async def chat_stream(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """以 SSE 流式返回对话内容。

    由于流式响应在依赖会话关闭后才产生内容，此处单独创建数据库会话，
    避免会话生命周期问题。
    """

    async def event_stream():
        async with AsyncSessionLocal() as db:
            try:
                async for chunk in chat_service.chat_stream(
                    db,
                    user_id=current_user.id,
                    question=payload.question,
                    session_id=payload.session_id,
                    knowledge_base_ids=payload.knowledge_base_ids,
                ):
                    yield chunk
            except Exception as exc:  # noqa: BLE001
                # 兜底：将异常转为 SSE 错误帧，避免连接静默中断
                import json

                yield f"data: {json.dumps({'type': 'error', 'message': str(exc)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get(
    "/history",
    response_model=PaginatedResponse[ChatSessionResponse],
    summary="会话历史列表",
)
async def history(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[ChatSessionResponse]:
    """分页获取当前用户的会话列表。"""
    return await chat_service.get_history(db, current_user.id, page, page_size)


@router.get(
    "/history/{session_id}",
    response_model=list[ChatMessageResponse],
    summary="会话消息详情",
)
async def history_detail(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatMessageResponse]:
    """获取指定会话的全部消息。"""
    return await chat_service.get_session(db, current_user.id, session_id)


@router.delete("/history/{session_id}", summary="删除会话")
async def delete_history(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """删除指定会话及其消息。"""
    await chat_service.delete_session(db, current_user.id, session_id)
    return {"message": "会话已删除", "session_id": session_id}


@router.patch(
    "/history/{session_id}",
    response_model=ChatSessionResponse,
    summary="重命名会话",
)
async def rename_session(
    session_id: int,
    payload: SessionRenameRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionResponse:
    """重命名指定会话标题。"""
    return await chat_service.rename_session(
        db, current_user.id, session_id, payload.title
    )


@router.post("/chat/messages/{message_id}/feedback", summary="提交消息反馈")
async def submit_feedback(
    message_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """提交对 AI 回答的反馈（点赞/点踩/评分）。

    请求体示例：
    - {"feedback_type": "upvote", "rating": 5, "feedback_text": "回答很准确"}
    - {"feedback_type": "downvote", "rating": 2, "feedback_text": "回答偏离主题"}
    """
    feedback_type = payload.get("feedback_type", "")
    rating = payload.get("rating")
    feedback_text = payload.get("feedback_text")

    feedback_id = await feedback_recorder.record_feedback(
        db,
        user_id=current_user.id,
        message_id=message_id,
        feedback_type=feedback_type,
        rating=rating,
        text=feedback_text,
    )

    # 点踩时反向标注命中（点踩视为未命中）
    if feedback_type == "downvote":
        try:
            await recall_metrics.update_hit_by_message(db, message_id, hit=False)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"反向标注命中率失败: {exc}")
    elif feedback_type == "upvote":
        try:
            await recall_metrics.update_hit_by_message(db, message_id, hit=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"反向标注命中率失败: {exc}")

    if feedback_id is None:
        return {"message": "反馈提交失败（可能已禁用指标采集）", "feedback_id": None}
    return {"message": "反馈已记录", "feedback_id": feedback_id}


@router.get("/chat/messages/{message_id}/feedback", summary="查询消息反馈")
async def get_feedback(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """查询当前用户对指定消息的反馈记录。"""
    feedback = await feedback_recorder.get_feedback(
        db, user_id=current_user.id, message_id=message_id
    )
    if feedback is None:
        return {"feedback_type": None, "rating": None, "feedback_text": None}
    return {
        "feedback_type": feedback.feedback_type,
        "rating": feedback.rating,
        "feedback_text": feedback.feedback_text,
    }
