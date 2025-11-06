"""
AI聊天API路由
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.schemas.chat import (
    ChatMessagesResponse,
    ChatRequest,
    ChatResponse,
    ChatStreamRequest,
    ConversationDeleteResponse,
    ConversationListResponse,
)
from app.services.ai_service import AIService

router = APIRouter()


async def get_ai_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> AIService:
    """获取AI服务依赖"""
    return AIService(db=db, user_id=current_user.id)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    current_user: CurrentUser,
    ai_service: Annotated[AIService, Depends(get_ai_service)],
):
    """
    发送聊天消息

    支持AI Function Calling，可以调用服务器管理工具：
    - list_servers: 列出服务器
    - get_server_metrics: 获取服务器指标
    - execute_command: 执行命令
    - get_server_info: 获取服务器信息

    示例对话：
    - "列出我的所有服务器"
    - "检查服务器的CPU使用率"
    - "在production服务器上执行uptime命令"

    需要Bearer Token认证
    """
    try:
        result = await ai_service.chat(
            message=chat_request.message,
            conversation_id=chat_request.conversation_id,
        )

        return ChatResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"聊天处理失败: {str(e)}",
        )


@router.post("/chat/stream")
async def chat_stream(
    chat_request: ChatStreamRequest,
    current_user: CurrentUser,
    ai_service: Annotated[AIService, Depends(get_ai_service)],
):
    """
    流式聊天

    返回Server-Sent Events (SSE)格式的流式响应

    注意：流式模式下Function Calling支持有限

    需要Bearer Token认证
    """

    async def generate():
        try:
            async for chunk in ai_service.stream_chat(
                message=chat_request.message,
                conversation_id=chat_request.conversation_id,
            ):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    current_user: CurrentUser,
    ai_service: Annotated[AIService, Depends(get_ai_service)],
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """
    获取会话列表

    返回用户的所有AI会话，按最后消息时间倒序排列

    需要Bearer Token认证
    """
    try:
        result = await ai_service.get_conversations(page=page, size=size)
        return ConversationListResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话列表失败: {str(e)}",
        )


@router.get("/conversations/{conversation_id}", response_model=ChatMessagesResponse)
async def get_conversation_messages(
    conversation_id: UUID,
    current_user: CurrentUser,
    ai_service: Annotated[AIService, Depends(get_ai_service)],
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=100, description="每页数量"),
):
    """
    获取会话的消息历史

    返回指定会话的所有消息，按时间顺序排列

    需要Bearer Token认证
    """
    try:
        result = await ai_service.get_conversation_messages(
            conversation_id=conversation_id,
            page=page,
            size=size,
        )
        return ChatMessagesResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取消息历史失败: {str(e)}",
        )


@router.delete("/conversations/{conversation_id}", response_model=ConversationDeleteResponse)
async def delete_conversation(
    conversation_id: UUID,
    current_user: CurrentUser,
    ai_service: Annotated[AIService, Depends(get_ai_service)],
):
    """
    删除会话

    删除指定会话及其所有消息

    需要Bearer Token认证
    """
    try:
        success = await ai_service.delete_conversation(conversation_id=conversation_id)

        if success:
            return ConversationDeleteResponse(
                success=True,
                message="会话已删除",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除会话失败",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除会话失败: {str(e)}",
        )
