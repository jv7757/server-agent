"""
服务器模型
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.audit import AuditLog
    from app.models.chat import ChatHistory
    from app.models.metric import ServerMetric
    from app.models.permission import UserServerPermission
    from app.models.user import User


class Server(Base):
    """服务器模型"""

    __tablename__ = "servers"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, default=22, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # 所有者
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # SSH认证信息（加密存储）
    ssh_username: Mapped[str | None] = mapped_column(String(100))
    ssh_password_encrypted: Mapped[str | None] = mapped_column(Text)
    ssh_key_encrypted: Mapped[str | None] = mapped_column(Text)

    # 服务器标签（JSON数组）
    tags: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # 连接状态
    status: Mapped[str] = mapped_column(
        String(20), default="unknown", nullable=False, index=True
    )  # online, offline, error, unknown
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关系
    owner: Mapped["User"] = relationship("User", back_populates="servers")
    metrics: Mapped[list["ServerMetric"]] = relationship(
        "ServerMetric", back_populates="server", cascade="all, delete-orphan"
    )
    permissions: Mapped[list["UserServerPermission"]] = relationship(
        "UserServerPermission", back_populates="server", cascade="all, delete-orphan"
    )
    chat_history: Mapped[list["ChatHistory"]] = relationship("ChatHistory", back_populates="server")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="server")

    def __repr__(self) -> str:
        return f"<Server {self.name} ({self.host})>"

    @property
    def is_online(self) -> bool:
        """是否在线"""
        return self.status == "online"

    @property
    def connection_string(self) -> str:
        """连接字符串"""
        return f"{self.ssh_username}@{self.host}:{self.port}"
