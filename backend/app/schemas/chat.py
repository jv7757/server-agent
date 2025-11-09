"""
聊天相关的Pydantic模式
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ========== 聊天请求 ==========


class ChatRequest(BaseModel):
    """聊天请求模式"""

    message: str = Field(..., min_length=1, description="用户消息")
    conversation_id: UUID | None = Field(None, description="会话ID（可选，不提供则创建新会话）")
    server_id: UUID | None = Field(None, description="默认服务器ID（可选，作为工具调用的上下文）")


class ChatStreamRequest(BaseModel):
    """流式聊天请求模式"""

    message: str = Field(..., min_length=1, description="用户消息")
    conversation_id: UUID | None = Field(None, description="会话ID（可选，不提供则创建新会话）")
    server_id: UUID | None = Field(None, description="默认服务器ID（可选，作为工具调用的上下文）")


# ========== 聊天响应 ==========


class ChatResponse(BaseModel):
    """聊天响应模式"""

    conversation_id: str = Field(..., description="会话ID")
    message: str = Field(..., description="AI响应消息")
    iterations: int | None = Field(None, description="工具调用迭代次数")
    error: str | None = Field(None, description="错误信息")


class ChatMessageResponse(BaseModel):
    """单条聊天消息响应"""

    id: str
    role: str
    content: str
    created_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v):
        """将 UUID 转换为字符串"""
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


class ChatMessagesResponse(BaseModel):
    """聊天消息列表响应"""

    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="每页数量")
    items: list[ChatMessageResponse] = Field(..., description="消息列表")


# ========== 会话响应 ==========


class ConversationListItem(BaseModel):
    """会话列表项"""

    conversation_id: str
    last_message: str
    last_message_at: datetime
    role: str


class ConversationListResponse(BaseModel):
    """会话列表响应"""

    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="每页数量")
    items: list[ConversationListItem] = Field(..., description="会话列表")


class ConversationDeleteResponse(BaseModel):
    """删除会话响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="提示消息")
