"""
AI聊天历史模型
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.server import Server


class ChatHistory(Base):
    """AI聊天历史模型"""

    __tablename__ = "chat_history"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # 外键
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    server_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("servers.id", ondelete="SET NULL"),
        index=True
    )

    # 消息信息
    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # 元数据（存储命令执行结果、工具调用等）
    metadata: Mapped[dict | None] = mapped_column(JSONB)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="chat_history")
    server: Mapped["Server | None"] = relationship("Server", back_populates="chat_history")

    def __repr__(self) -> str:
        return f"<ChatHistory {self.role}: {self.content[:50]}>"

    @property
    def is_user_message(self) -> bool:
        """是否为用户消息"""
        return self.role == "user"

    @property
    def is_assistant_message(self) -> bool:
        """是否为助手消息"""
        return self.role == "assistant"

    @property
    def is_system_message(self) -> bool:
        """是否为系统消息"""
        return self.role == "system"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "server_id": str(self.server_id) if self.server_id else None,
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
